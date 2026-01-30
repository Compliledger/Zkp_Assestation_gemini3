"""Algorand anchoring smart contract (PyTeal).

Stores anchor records in application boxes keyed by package_id.
"""

from pyteal import (
    App,
    Approve,
    Assert,
    Bytes,
    Concat,
    Expr,
    If,
    Int,
    Len,
    OnComplete,
    Return,
    Seq,
    Subroutine,
    TealType,
    Txn,
    TxnType,
)


MAX_PACKAGE_ID_LEN = 64
HASH_LEN = 32


@Subroutine(TealType.bytes)
def _box_key():
    return Txn.application_args[1]


@Subroutine(TealType.bytes)
def _box_value():
    package_hash = Txn.application_args[2]
    merkle_root = Txn.application_args[3]
    ts = Txn.application_args[4]
    return Concat(package_hash, merkle_root, ts, Txn.sender())


def approval_program():
    is_create = Txn.application_id() == Int(0)

    on_create = Seq(
        [
            Assert(Txn.type_enum() == TxnType.ApplicationCall),
            Approve(),
        ]
    )

    on_update = Return(Int(0))
    on_delete = Return(Int(0))

    is_anchor = Txn.application_args.length() == Int(5)
    is_read = Txn.application_args.length() == Int(2)

    on_anchor = Seq(
        [
            Assert(Txn.application_args[0] == Bytes("anchor")),
            Assert(Len(Txn.application_args[1]) <= Int(MAX_PACKAGE_ID_LEN)),
            Assert(Len(Txn.application_args[2]) == Int(HASH_LEN)),
            Assert(Len(Txn.application_args[3]) == Int(HASH_LEN)),
            Assert(Len(Txn.application_args[4]) == Int(8)),
            App.box_put(_box_key(), _box_value()),
            Approve(),
        ]
    )

    on_read = Seq(
        [
            Assert(Txn.application_args[0] == Bytes("read")),
            Approve(),
        ]
    )

    program = Seq(
        [
            Assert(Txn.on_completion() != OnComplete.OptIn),
            If(
                is_create,
                on_create,
                If(
                    Txn.on_completion() == OnComplete.UpdateApplication,
                    on_update,
                    If(
                        Txn.on_completion() == OnComplete.DeleteApplication,
                        on_delete,
                        If(is_anchor, on_anchor, If(is_read, on_read, Return(Int(0))))
                    ),
                ),
            ),
        ]
    )

    return program


def clear_state_program():
    return Approve()
