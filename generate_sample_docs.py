import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

def create_pdf(filename: str, title: str, pages_content: list[str]):
    """Helper script to create sample PDF documents for testing RAG chatbot."""
    docs_dir = os.path.join(os.path.dirname(__file__), "documents")
    os.makedirs(docs_dir, exist_ok=True)
    filepath = os.path.join(docs_dir, filename)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        spaceAfter=20,
        textColor='#1a365d'
    )
    heading_style = ParagraphStyle(
        'DocHeading',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        spaceBefore=12,
        spaceAfter=8,
        textColor='#2b6cb0'
    )
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['BodyText'],
        fontSize=10,
        leading=15,
        spaceAfter=10
    )

    story = []
    # Document Header
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 10))

    for page_idx, content in enumerate(pages_content):
        if page_idx > 0:
            story.append(PageBreak())
        
        # Add Page Content
        for line in content.strip().split("\n\n"):
            if line.startswith("## "):
                story.append(Paragraph(line.replace("## ", ""), heading_style))
            else:
                story.append(Paragraph(line, body_style))
            story.append(Spacer(1, 6))

    doc.build(story)
    print(f"Generated sample PDF: {filepath}")

def generate_all():
    # 1. Leave Policy
    leave_pages = [
        """## Section 1: Annual Leave Entitlement
Employees receive 20 days of paid annual leave per calendar year. Annual leave accrues at a rate of 1.66 days per month worked. Full-time employees are eligible for annual leave immediately upon starting employment.

## Section 2: Requesting Leave
All leave requests must be submitted through the HR Portal at least 5 business days in advance for leave exceeding 3 consecutive days. Emergency leave requires notification to your manager before 9:00 AM on the day of absence.""",
        """## Section 3: Carry Forward Policy
Unused annual leave may be carried forward up to a maximum of 5 days into the following calendar year. Carried-forward leave must be used before March 31st of the new year, or it will be forfeited.

## Section 4: Sick Leave & Parental Leave
Employees receive 10 days of paid sick leave per year. A medical certificate is required for sick leave exceeding 2 consecutive days. Parental leave provides 12 weeks of fully paid leave for primary caregivers."""
    ]
    create_pdf("leave_policy.pdf", "Company Leave Policy (2025)", leave_pages)

    # 2. Refund Policy
    refund_pages = [
        """## Section 1: Product Refund Standard Window
Customers can request a full refund within 30 days of the original purchase date. To be eligible for a refund, the product must be unused, in its original packaging, and accompanied by proof of purchase or receipt.

## Section 2: Non-Refundable Items
Digital downloads, customized software licenses, and gift cards are strictly non-refundable once issued or downloaded, except where required by applicable local consumer law.""",
        """## Section 3: Processing Refunds
Approved refunds will be processed back to the original payment method within 5 to 7 business days. Shipping costs are non-refundable unless the return is due to a verifiable company defect or error.

## Section 4: Exchanges & Return Shipping
Customers are responsible for paying their own return shipping costs unless the item arrived damaged or incorrect. Product exchanges can be initiated online through the customer portal."""
    ]
    create_pdf("refund_policy.pdf", "Customer Refund Policy", refund_pages)

    # 3. Remote Work Policy
    remote_pages = [
        """## Section 1: Remote Work Eligibility
Full-time employees who have completed their initial 90-day probationary period are eligible to apply for remote work. Hybrid schedules allow up to 3 work-from-home days per week with manager approval.

## Section 2: Core Working Hours
All remote team members must be available and reachable online during core business hours from 10:00 AM to 4:00 PM local time to ensure effective team collaboration.""",
        """## Section 3: Home Office Equipment Stipend
The company provides a one-time home office setup stipend of $500 upon approval of a remote work arrangement. This stipend covers monitors, ergonomic chairs, keyboards, and mice.

## Section 4: Information Security
Remote workers must connect to the corporate network using the company-provided VPN. Work must only be performed on company-issued encrypted laptops."""
    ]
    create_pdf("remote_work_policy.pdf", "Remote Work Policy", remote_pages)

    # 4. Expense Policy
    expense_pages = [
        """## Section 1: Travel & Business Expenses
Employees traveling on authorized company business will be reimbursed for reasonable and necessary travel expenses. Flight bookings must be made in Economy class for trips under 6 hours.

## Section 2: Daily Meal Allowance
The daily meal allowance cap for business travel is $75 per day. Itemized receipts are required for all individual meal expenses exceeding $15.""",
        """## Section 3: Expense Report Submission
Expense reports must be submitted within 14 days of returning from business travel or incurring the expense. Late submissions past 30 days will not be reimbursed without Vice President approval.

## Section 4: Taxi & Rideshare Usage
Rideshare services (Uber, Lyft) and taxis are reimbursable when traveling between airport, hotel, and client office locations. Personal mileage is reimbursed at $0.65 per mile."""
    ]
    create_pdf("expense_policy.pdf", "Company Expense & Travel Policy", expense_pages)

    # 5. Employee Handbook Overview
    handbook_pages = [
        """## Section 1: Code of Conduct & Values
Our company values integrity, innovation, and mutual respect. We maintain a zero-tolerance policy for harassment, discrimination, or unethical conduct in any workplace setting.

## Section 2: Standard Working Hours
Standard office working hours are Monday through Friday, 9:00 AM to 5:00 PM, with a one-hour lunch break. Flexible working schedules can be arranged with your direct manager.""",
        """## Section 3: Health Benefits Overview
Full-time employees receive comprehensive medical, dental, and vision insurance starting on their first day of employment. The company pays 85% of premium costs for employees and 60% for dependents.

## Section 4: Learning & Professional Development
Employees receive an annual learning stipend of $1,000 to attend industry conferences, enroll in online courses, or purchase professional books relevant to their role."""
    ]
    create_pdf("employee_handbook.pdf", "General Employee Handbook Summary", handbook_pages)

if __name__ == "__main__":
    generate_all()
