"""
Test LaTeX generation with actual note content
"""
import sys
import os
# Add the parent directory (backend) to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from pdf_generation.latex_service import latex_service
from pdf_generation.pdf_compiler import pdf_compiler

# Your actual note content (from the screenshot)
test_content = """
## **Economic Significance**

Hong Kong is not only a bustling urban center but also a major global financial hub. Its economy is characterized by:

- **Free Market Economy:**
  - Hong Kong operates under a laissez-faire economic policy, which encourages trade and investment.

- **Financial Services:**
  - Home to an array of banks, financial institutions, and stock exchanges, Hong Kong is a leading player in global finance:
    - **Hong Kong Stock Exchange (HKEX)** ranks among the largest in the world.
    - Numerous multinational corporations establish their Asian headquarters here.

- **Tourism:**
  - Attractions include:
    - **Victoria Peak**: Offering breathtaking views of the harbor.
    - **Tsim Sha Tsui**: A vibrant area known for shopping and dining.
    - **Historical Sites**: Temples, museums, and colonial-era architecture draw millions of tourists annually.

---

## **Cultural Heritage and Lifestyle**
"""

print("="*60)
print("TESTING LATEX GENERATION")
print("="*60)

# Test 1: Generate LaTeX
print("\n1. Generating LaTeX document...")
latex_doc = latex_service.generate_latex_document(
    content=test_content,
    title="Hong Kong: Economic and Cultural Overview",
    author="Student"
)

print(f"\nGenerated LaTeX ({len(latex_doc)} characters)")
print("\nFirst 500 characters of LaTeX:")
print("-" * 60)
print(latex_doc[:500])
print("-" * 60)

# Save the .tex file so you can see it
tex_output_path = "generated_pdfs/test_hongkong.tex"
os.makedirs("generated_pdfs", exist_ok=True)
with open(tex_output_path, 'w', encoding='utf-8') as f:
    f.write(latex_doc)
print(f"\nSaved .tex file to: {tex_output_path}")

# Test 2: Compile to PDF
print("\n2. Compiling to PDF...")
pdf_path, tex_path, error = pdf_compiler.compile_to_pdf(
    latex_content=latex_doc,
    output_filename="test_hongkong",
    save_tex=True
)

if error:
    print(f"\nERROR: {error}")
else:
    print(f"\nSUCCESS!")
    print(f"PDF: {pdf_path}")
    print(f"TEX: {tex_path}")
    print(f"\nOpen the PDF to see the beautiful formatted output!")

print("\n" + "="*60)
