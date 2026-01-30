"""
PDF Report Generator
Generates professional PDF reports for attestation packages
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field
import json

from app.core.attestation.package_builder import AttestationPackage
from app.utils.errors import ValidationError


class PDFReport(BaseModel):
    """
    PDF report metadata
    """
    report_id: str = Field(..., description="Report identifier")
    package_id: str = Field(..., description="Associated package ID")
    file_path: str = Field(..., description="Path to PDF file")
    file_size: int = Field(..., description="File size in bytes")
    page_count: int = Field(..., description="Number of pages")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PDFGenerator:
    """
    Generates PDF reports from attestation packages
    
    Note: This is a simplified implementation. In production, use libraries like:
    - ReportLab
    - WeasyPrint
    - xhtml2pdf
    """
    
    def __init__(self, output_path: Optional[Path] = None):
        """
        Initialize PDF generator
        
        Args:
            output_path: Path for PDF outputs
        """
        self.output_path = output_path or Path("./exports/pdf")
        self.output_path.mkdir(parents=True, exist_ok=True)
    
    def generate_attestation_report(
        self,
        package: AttestationPackage,
        include_evidence: bool = True,
        include_proofs: bool = True,
        template: str = "standard"
    ) -> PDFReport:
        """
        Generate PDF attestation report
        
        Args:
            package: Attestation package
            include_evidence: Include evidence details
            include_proofs: Include proof details
            template: Report template to use
        
        Returns:
            PDFReport metadata
        """
        # Generate HTML content
        html_content = self._generate_html(
            package,
            include_evidence=include_evidence,
            include_proofs=include_proofs,
            template=template
        )
        
        # Generate PDF filename
        filename = f"{package.package_id}_report.pdf"
        file_path = self.output_path / filename
        
        # Convert HTML to PDF (simulated)
        # In production, use actual PDF library
        pdf_content = self._html_to_pdf(html_content)
        
        # Write PDF
        file_path.write_bytes(pdf_content)
        
        # Create report metadata
        report = PDFReport(
            report_id=f"report_{package.package_id}",
            package_id=package.package_id,
            file_path=str(file_path),
            file_size=len(pdf_content),
            page_count=self._estimate_page_count(html_content)
        )
        
        return report
    
    def generate_executive_summary(
        self,
        package: AttestationPackage
    ) -> PDFReport:
        """
        Generate executive summary PDF
        
        Args:
            package: Attestation package
        
        Returns:
            PDFReport metadata
        """
        html_content = self._generate_executive_summary_html(package)
        
        filename = f"{package.package_id}_executive_summary.pdf"
        file_path = self.output_path / filename
        
        pdf_content = self._html_to_pdf(html_content)
        file_path.write_bytes(pdf_content)
        
        report = PDFReport(
            report_id=f"summary_{package.package_id}",
            package_id=package.package_id,
            file_path=str(file_path),
            file_size=len(pdf_content),
            page_count=1
        )
        
        return report
    
    def generate_compliance_report(
        self,
        package: AttestationPackage,
        framework: str
    ) -> PDFReport:
        """
        Generate framework-specific compliance report
        
        Args:
            package: Attestation package
            framework: Compliance framework (SOC2, ISO27001, etc.)
        
        Returns:
            PDFReport metadata
        """
        html_content = self._generate_compliance_html(package, framework)
        
        filename = f"{package.package_id}_{framework}_compliance.pdf"
        file_path = self.output_path / filename
        
        pdf_content = self._html_to_pdf(html_content)
        file_path.write_bytes(pdf_content)
        
        report = PDFReport(
            report_id=f"compliance_{package.package_id}_{framework}",
            package_id=package.package_id,
            file_path=str(file_path),
            file_size=len(pdf_content),
            page_count=self._estimate_page_count(html_content)
        )
        
        return report
    
    def _generate_html(
        self,
        package: AttestationPackage,
        include_evidence: bool,
        include_proofs: bool,
        template: str
    ) -> str:
        """Generate HTML content for PDF"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{package.title}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 40px;
            color: #333;
        }}
        .header {{
            border-bottom: 3px solid #0066cc;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #0066cc;
            margin: 0;
        }}
        .section {{
            margin: 30px 0;
        }}
        .section h2 {{
            color: #0066cc;
            border-bottom: 1px solid #ccc;
            padding-bottom: 10px;
        }}
        .metadata {{
            background: #f5f5f5;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .metadata-item {{
            margin: 10px 0;
        }}
        .metadata-label {{
            font-weight: bold;
            display: inline-block;
            width: 200px;
        }}
        .evidence-item, .proof-item {{
            background: #fafafa;
            padding: 15px;
            margin: 10px 0;
            border-left: 3px solid #0066cc;
        }}
        .footer {{
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #ccc;
            font-size: 12px;
            color: #666;
        }}
        .signature-box {{
            border: 1px solid #ccc;
            padding: 20px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{package.title}</h1>
        <p>{package.description}</p>
    </div>
    
    <div class="section">
        <h2>Attestation Information</h2>
        <div class="metadata">
            <div class="metadata-item">
                <span class="metadata-label">Package ID:</span>
                <span>{package.package_id}</span>
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Claim ID:</span>
                <span>{package.claim_id}</span>
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Attestation Type:</span>
                <span>{package.attestation_type}</span>
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Status:</span>
                <span>{package.status.value}</span>
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Compliance Framework:</span>
                <span>{package.compliance_framework or 'N/A'}</span>
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Valid From:</span>
                <span>{package.valid_from.strftime('%Y-%m-%d')}</span>
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Valid Until:</span>
                <span>{package.valid_until.strftime('%Y-%m-%d') if package.valid_until else 'No expiration'}</span>
            </div>
        </div>
    </div>
    
    <div class="section">
        <h2>Issuer Information</h2>
        <div class="metadata">
            <div class="metadata-item">
                <span class="metadata-label">Name:</span>
                <span>{package.issuer.get('name', 'N/A')}</span>
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Organization:</span>
                <span>{package.issuer.get('organization', 'N/A')}</span>
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Email:</span>
                <span>{package.issuer.get('email', 'N/A')}</span>
            </div>
        </div>
    </div>
"""
        
        # Add evidence section
        if include_evidence and package.evidence_bundles:
            html += """
    <div class="section">
        <h2>Evidence Bundles</h2>
"""
            for bundle in package.evidence_bundles:
                html += f"""
        <div class="evidence-item">
            <p><strong>Bundle ID:</strong> {bundle['bundle_id']}</p>
            <p><strong>Evidence Count:</strong> {bundle['evidence_count']}</p>
            <p><strong>Merkle Root:</strong> {bundle['merkle_root'][:16]}...</p>
            <p><strong>Created:</strong> {bundle.get('created_at', 'N/A')}</p>
        </div>
"""
            html += "    </div>\n"
        
        # Add proofs section
        if include_proofs and package.proofs:
            html += """
    <div class="section">
        <h2>Zero-Knowledge Proofs</h2>
"""
            for proof in package.proofs:
                html += f"""
        <div class="proof-item">
            <p><strong>Proof ID:</strong> {proof['proof_id']}</p>
            <p><strong>Circuit Type:</strong> {proof['circuit_type']}</p>
            <p><strong>Template:</strong> {proof['template_id']}</p>
            <p><strong>Proof Hash:</strong> {proof['proof_hash'][:32]}...</p>
            <p><strong>Proving Time:</strong> {proof['proving_time']:.2f}s</p>
        </div>
"""
            html += "    </div>\n"
        
        # Add signature section
        if package.signature:
            html += f"""
    <div class="section">
        <h2>Digital Signature</h2>
        <div class="signature-box">
            <p><strong>Signature Algorithm:</strong> {package.signature_algorithm}</p>
            <p><strong>Signature:</strong> {package.signature[:64]}...</p>
            <p><strong>Signed At:</strong> {package.signed_at.strftime('%Y-%m-%d %H:%M:%S') if package.signed_at else 'N/A'}</p>
            <p><strong>Package Hash:</strong> {package.package_hash}</p>
        </div>
    </div>
"""
        
        html += f"""
    <div class="footer">
        <p>Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        <p>ZKP Attestation Agent v1.0</p>
    </div>
</body>
</html>
"""
        return html
    
    def _generate_executive_summary_html(self, package: AttestationPackage) -> str:
        """Generate executive summary HTML"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Executive Summary - {package.title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ text-align: center; margin-bottom: 40px; }}
        .summary-box {{ background: #f0f8ff; padding: 20px; border-radius: 5px; margin: 20px 0; }}
        .stat {{ display: inline-block; margin: 15px 30px; text-align: center; }}
        .stat-value {{ font-size: 32px; font-weight: bold; color: #0066cc; }}
        .stat-label {{ font-size: 14px; color: #666; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Executive Summary</h1>
        <h2>{package.title}</h2>
    </div>
    
    <div class="summary-box">
        <h3>Attestation Overview</h3>
        <p>{package.description}</p>
        
        <div style="text-align: center; margin: 30px 0;">
            <div class="stat">
                <div class="stat-value">{len(package.evidence_bundles)}</div>
                <div class="stat-label">Evidence Bundles</div>
            </div>
            <div class="stat">
                <div class="stat-value">{len(package.proofs)}</div>
                <div class="stat-label">ZKP Proofs</div>
            </div>
            <div class="stat">
                <div class="stat-value">{package.status.value.upper()}</div>
                <div class="stat-label">Status</div>
            </div>
        </div>
        
        <p><strong>Compliance Framework:</strong> {package.compliance_framework or 'Custom'}</p>
        <p><strong>Valid Period:</strong> {package.valid_from.strftime('%Y-%m-%d')} to {package.valid_until.strftime('%Y-%m-%d') if package.valid_until else 'No expiration'}</p>
        <p><strong>Issuer:</strong> {package.issuer.get('name', 'N/A')}</p>
    </div>
</body>
</html>
"""
        return html
    
    def _generate_compliance_html(self, package: AttestationPackage, framework: str) -> str:
        """Generate compliance-specific HTML"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{framework} Compliance Report - {package.title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ border-bottom: 3px solid #0066cc; padding-bottom: 20px; }}
        .control {{ background: #fafafa; padding: 15px; margin: 10px 0; border-left: 3px solid #28a745; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{framework} Compliance Report</h1>
        <h2>{package.title}</h2>
    </div>
    
    <div class="section">
        <h2>Compliance Summary</h2>
        <p>This report demonstrates compliance with {framework} requirements through zero-knowledge proofs.</p>
        <p><strong>Assessment Date:</strong> {package.assessment_date.strftime('%Y-%m-%d')}</p>
        <p><strong>Evidence Bundles:</strong> {len(package.evidence_bundles)}</p>
        <p><strong>ZKP Proofs:</strong> {len(package.proofs)}</p>
    </div>
    
    <div class="section">
        <h2>Evidence & Proofs</h2>
        <p>All evidence has been cryptographically verified through zero-knowledge proofs.</p>
    </div>
</body>
</html>
"""
        return html
    
    def _html_to_pdf(self, html_content: str) -> bytes:
        """
        Convert HTML to PDF
        
        In production, use libraries like:
        - WeasyPrint: weasyprint.HTML(string=html_content).write_pdf()
        - xhtml2pdf: pisa.CreatePDF(html_content)
        - ReportLab: Build PDF from scratch
        
        For now, simulate PDF generation
        """
        # Simulate PDF by storing HTML as bytes
        # In production, use actual PDF library
        pdf_header = b"%PDF-1.4\n"
        pdf_content = html_content.encode('utf-8')
        return pdf_header + pdf_content
    
    def _estimate_page_count(self, html_content: str) -> int:
        """Estimate PDF page count from HTML length"""
        # Rough estimate: 3000 characters per page
        char_count = len(html_content)
        return max(1, (char_count // 3000) + 1)
    
    def get_report_path(self, report: PDFReport) -> Path:
        """Get path to PDF report file"""
        return Path(report.file_path)
    
    def list_reports(self) -> List[PDFReport]:
        """List all generated reports"""
        reports = []
        
        for pdf_file in self.output_path.glob("*.pdf"):
            # Try to load metadata if exists
            metadata_file = pdf_file.with_suffix('.json')
            if metadata_file.exists():
                try:
                    report = PDFReport.parse_raw(metadata_file.read_text())
                    reports.append(report)
                except:
                    pass
        
        return reports
