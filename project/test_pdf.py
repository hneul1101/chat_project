from utils import generate_pdf_report
import os

# Dummy data
chat_history = [
    {"role": "user", "content": "삼성전자 분석해줘"},
    {"role": "assistant", "content": "삼성전자는 현재 7만원입니다. **강력 매수** 추천합니다."}
]
user_profile = "aggressive"

print("Testing PDF generation...")
pdf_file, error = generate_pdf_report(chat_history, user_profile)

if error:
    print(f"FAILED: {error}")
else:
    print(f"SUCCESS: Generated {pdf_file}")
    # Check if file exists
    if os.path.exists(pdf_file):
        print("File exists.")
        # Clean up
        os.remove(pdf_file)
        print("Cleaned up.")
    else:
        print("File does not exist!")
