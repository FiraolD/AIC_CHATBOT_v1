# backend/scripts/seed_documents.py
"""Create sample insurance documents for testing"""
from pathlib import Path
import csv

def create_sample_data():
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    # Create sample CSV
    csv_path = data_dir / "insurance_knowledge.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['type', 'question', 'answer'])
        
        # Add high-quality insurance content
        writer.writerow(['Claims Process', 'How do I file a claim?', 
                       'Call +251-11-6185000 within 24 hours, submit claim form online, attach required documents, schedule inspection, receive payment in ETB within 7 working days'])
        
        writer.writerow(['Motor Insurance', 'What does comprehensive motor insurance cover?',
                       'Accidents, theft, fire, vandalism, natural disasters, and third-party liability'])
        
        writer.writerow(['Life Insurance', 'What is term life insurance?',
                       'Provides coverage for specific period (5, 10, 15 years) with affordable premiums'])
        
        writer.writerow(['Contact Information', 'Support Contact Info',
                       'Phone: +251-11-6185000, Email: info@awashinsurance.com, Address: Churchill Road, Addis Ababa'])

    print(f"✅ Created sample data at {csv_path}")

if __name__ == "__main__":
    create_sample_data()