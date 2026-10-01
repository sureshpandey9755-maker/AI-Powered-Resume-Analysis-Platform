from app.services.parser import extract_text


file_path = "sample_resume.pdf"

text = extract_text(file_path)

print("\n========== RESUME TEXT ==========\n")

print(text)