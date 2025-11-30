
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def create_contract_pdf(filename):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    c.drawString(100, 750, "NON-DISCLOSURE AGREEMENT")
    c.drawString(100, 730, "This Non-Disclosure Agreement (the 'Agreement') is entered into by and between:")
    c.drawString(100, 710, "Party A: Acme Corp, a Delaware corporation ('Disclosing Party')")
    c.drawString(100, 690, "Party B: Beta Inc, a California corporation ('Receiving Party')")
    c.drawString(100, 670, "Effective Date: January 1, 2024")
    
    c.drawString(100, 640, "1. Confidential Information")
    c.drawString(100, 625, "Confidential Information shall include all data, trade secrets, and business plans.")
    
    c.drawString(100, 600, "2. Term")
    c.drawString(100, 585, "This Agreement shall remain in effect for a period of two (2) years.")
    
    c.drawString(100, 560, "3. Governing Law")
    c.drawString(100, 545, "This Agreement shall be governed by the laws of the State of New York.")
    
    c.drawString(100, 520, "4. Liability Cap")
    c.drawString(100, 505, "The total liability of either party shall not exceed $1,000,000 USD.")
    
    c.drawString(100, 480, "5. Termination")
    c.drawString(100, 465, "Either party may terminate this Agreement with thirty (30) days written notice.")
    
    c.save()

if __name__ == "__main__":
    create_contract_pdf("test_contract.pdf")
    print("Created test_contract.pdf")
