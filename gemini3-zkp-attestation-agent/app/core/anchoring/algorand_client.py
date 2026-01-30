"""Algorand client helpers for real on-chain anchoring (TestNet/MainNet).

This module intentionally keeps low-level SDK details in one place.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional
import base64
import time

from algosdk import account, encoding, logic, mnemonic
from algosdk.v2client import algod, indexer
from algosdk import transaction
from pyteal import compileTeal, Mode

from app.core.anchoring.algorand_contract import approval_program, clear_state_program


@dataclass(frozen=True)
class AlgorandClients:
    algod: algod.AlgodClient
    indexer: Optional[indexer.IndexerClient]


def make_clients(algod_url: str, algod_token: str = "", indexer_url: Optional[str] = None) -> AlgorandClients:
    algod_client = algod.AlgodClient(algod_token, algod_url)
    indexer_client = indexer.IndexerClient("", indexer_url) if indexer_url else None
    return AlgorandClients(algod=algod_client, indexer=indexer_client)


def mnemonic_to_keys(mn: str) -> tuple[str, str]:
    private_key = mnemonic.to_private_key(mn)
    address = account.address_from_private_key(private_key)
    return address, private_key


def compile_program(algod_client: algod.AlgodClient, teal_source: str) -> bytes:
    compiled = algod_client.compile(teal_source)
    return base64.b64decode(compiled["result"])


def deploy_anchor_app(
    algod_client: algod.AlgodClient,
    creator_addr: str,
    creator_private_key: str,
) -> dict[str, Any]:
    approval_teal = compileTeal(approval_program(), mode=Mode.Application, version=8)
    clear_teal = compileTeal(clear_state_program(), mode=Mode.Application, version=8)

    approval_bin = compile_program(algod_client, approval_teal)
    clear_bin = compile_program(algod_client, clear_teal)

    sp = algod_client.suggested_params()

    txn = transaction.ApplicationCreateTxn(
        sender=creator_addr,
        sp=sp,
        on_complete=transaction.OnComplete.NoOpOC,
        approval_program=approval_bin,
        clear_program=clear_bin,
        global_schema=transaction.StateSchema(num_uints=0, num_byte_slices=0),
        local_schema=transaction.StateSchema(num_uints=0, num_byte_slices=0),
    )

    signed = txn.sign(creator_private_key)
    txid = algod_client.send_transaction(signed)
    confirmed = transaction.wait_for_confirmation(algod_client, txid, 8)
    app_id = confirmed.get("application-index")

    return {
        "transaction_id": txid,
        "confirmed_round": confirmed.get("confirmed-round"),
        "app_id": app_id,
    }


def build_anchor_app_call_txn(
    algod_client: algod.AlgodClient,
    sender_addr: str,
    app_id: int,
    package_id: str,
    package_hash_hex: str,
    merkle_root_hex: str,
    timestamp: Optional[int] = None,
) -> transaction.ApplicationNoOpTxn:
    if timestamp is None:
        timestamp = int(time.time())

    pkg_key = package_id.encode("utf-8")
    pkg_hash = bytes.fromhex(package_hash_hex)
    merkle_root = bytes.fromhex(merkle_root_hex)
    ts_bytes = int(timestamp).to_bytes(8, "big")

    sp = algod_client.suggested_params()

    txn = transaction.ApplicationNoOpTxn(
        sender=sender_addr,
        sp=sp,
        index=app_id,
        app_args=[b"anchor", pkg_key, pkg_hash, merkle_root, ts_bytes],
        boxes=[(app_id, pkg_key)],
    )

    return txn


def get_application_address(app_id: int) -> str:
    return logic.get_application_address(app_id)


def build_funded_anchor_group(
    algod_client: algod.AlgodClient,
    sender_addr: str,
    app_id: int,
    package_id: str,
    package_hash_hex: str,
    merkle_root_hex: str,
    funding_amount_microalgos: int,
    timestamp: Optional[int] = None,
) -> list[transaction.Transaction]:
    """Build a group txn: fund app account + app-call to write box.

    Box usage increases minimum balance requirements. Funding the application address is
    required before the first box write.
    """
    sp = algod_client.suggested_params()
    app_addr = get_application_address(app_id)

    pay = transaction.PaymentTxn(
        sender=sender_addr,
        sp=sp,
        receiver=app_addr,
        amt=int(funding_amount_microalgos),
    )

    app_call = build_anchor_app_call_txn(
        algod_client=algod_client,
        sender_addr=sender_addr,
        app_id=app_id,
        package_id=package_id,
        package_hash_hex=package_hash_hex,
        merkle_root_hex=merkle_root_hex,
        timestamp=timestamp,
    )

    txns: list[transaction.Transaction] = [pay, app_call]
    transaction.assign_group_id(txns)
    return txns


def send_signed_txn_bytes(algod_client: algod.AlgodClient, signed_txn_bytes: bytes) -> dict[str, Any]:
    txid = algod_client.send_raw_transaction(signed_txn_bytes)
    confirmed = transaction.wait_for_confirmation(algod_client, txid, 8)

    return {
        "transaction_id": txid,
        "confirmed_round": confirmed.get("confirmed-round"),
        "txn": confirmed,
    }


def sign_and_send_group(
    algod_client: algod.AlgodClient,
    txns: list[transaction.Transaction],
    private_key: str,
) -> dict[str, Any]:
    signed = [t.sign(private_key) for t in txns]
    txid = algod_client.send_transactions(signed)
    confirmed = transaction.wait_for_confirmation(algod_client, txid, 8)
    return {
        "transaction_id": txid,
        "confirmed_round": confirmed.get("confirmed-round"),
        "txn": confirmed,
    }


def sign_and_send(algod_client: algod.AlgodClient, txn: transaction.Transaction, private_key: str) -> dict[str, Any]:
    signed = txn.sign(private_key)
    txid = algod_client.send_transaction(signed)
    confirmed = transaction.wait_for_confirmation(algod_client, txid, 8)
    return {
        "transaction_id": txid,
        "confirmed_round": confirmed.get("confirmed-round"),
        "txn": confirmed,
    }


def encode_unsigned_txn(txn: transaction.Transaction) -> str:
    raw = encoding.msgpack_encode(txn)
    return raw


def decode_b64_to_bytes(b64: str) -> bytes:
    return base64.b64decode(b64)


def read_anchor_box(algod_client: algod.AlgodClient, app_id: int, package_id: str) -> dict[str, Any]:
    name = package_id.encode("utf-8")
    box = algod_client.application_box_by_name(app_id, name)
    value = box.get("value")
    if isinstance(value, str):
        raw = base64.b64decode(value)
    else:
        raw = value

    if raw is None or len(raw) < 32 + 32 + 8 + 32:
        raise ValueError("Invalid or missing box value")

    package_hash = raw[0:32].hex()
    merkle_root = raw[32:64].hex()
    ts = int.from_bytes(raw[64:72], "big")
    sender = encoding.encode_address(raw[72:104])

    return {
        "package_id": package_id,
        "package_hash": package_hash,
        "merkle_root": merkle_root,
        "timestamp": ts,
        "anchored_by": sender,
    }
