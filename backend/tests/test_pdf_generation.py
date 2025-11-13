"""
Test script for PDF generation functionality
Run this to verify LaTeX and PDF services are working
"""
import sys
import os

# Add backend to path (parent directory)
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def test_latex_service():
    """Test LaTeX generation"""
    print("\n" + "="*50)
    print("Testing LaTeX Service")
    print("="*50)
    
    try:
        from pdf_generation.latex_service import latex_service
        
        test_content = """
# Introduction to Calculus

## Derivatives

The derivative of a function f(x) is defined as:
f'(x) = lim(h->0) [f(x+h) - f(x)] / h

**Theorem 1**: If f(x) = x^n, then f'(x) = nx^(n-1).

## Example

Consider f(x) = x^2. Then:
- f'(x) = 2x
- At x=3, the slope is f'(3) = 6

## Key Properties

1. Linearity: (af + bg)' = af' + bg'
2. Product Rule: (fg)' = f'g + fg'
3. Chain Rule: (f ∘ g)' = (f' ∘ g) * g'
"""
        
        latex_doc = latex_service.generate_latex_document(
            content=test_content,
            title="Calculus Notes",
            author="Test User"
        )
        
        print("LaTeX document generated successfully!")
        print(f"Document length: {len(latex_doc)} characters")
        print(f"First 200 chars:\n{latex_doc[:200]}...")
        
        return True, latex_doc
        
    except Exception as e:
        print(f"LaTeX service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_pdf_compiler(latex_content=None):
    """Test PDF compilation"""
    print("\n" + "="*50)
    print("Testing PDF Compiler")
    print("="*50)
    
    try:
        from pdf_generation.pdf_compiler import pdf_compiler
        
        # Use simple test document if no content provided
        if not latex_content:
            latex_content = r"""\documentclass[12pt]{article}
\usepackage{amsmath}
\title{Test Document}
\author{Test User}
\begin{document}
\maketitle

\section{Introduction}
This is a test document with math: $E = mc^2$

\subsection{Example}
Here's an equation:
\[
\int_0^\infty e^{-x^2} dx = \frac{\sqrt{\pi}}{2}
\]

\end{document}
"""
        
        print(f"Compiling LaTeX ({len(latex_content)} chars)...")
        
        pdf_path, tex_path, error = pdf_compiler.compile_to_pdf(
            latex_content=latex_content,
            output_filename="test_document",
            save_tex=True
        )
        
        if error:
            print(f"Compilation failed: {error}")
            return False
        
        if pdf_path:
            print(f"PDF compiled successfully!")
            print(f"PDF path: {pdf_path}")
            if tex_path:
                print(f"TeX path: {tex_path}")
            
            # Check file size
            if os.path.exists(pdf_path):
                size = os.path.getsize(pdf_path)
                print(f"PDF size: {size} bytes")
            
            return True
        else:
            print("PDF path is None")
            return False
            
    except Exception as e:
        print(f"PDF compiler test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """Test full integration: LaTeX generation + PDF compilation"""
    print("\n" + "="*50)
    print("Testing Full Integration")
    print("="*50)
    
    # Test LaTeX generation
    latex_success, latex_content = test_latex_service()
    
    if not latex_success:
        print("Integration test failed: LaTeX generation failed")
        return False
    
    # Test PDF compilation with generated LaTeX
    pdf_success = test_pdf_compiler(latex_content)
    
    if pdf_success:
        print("\n" + "="*50)
        print("ALL TESTS PASSED!")
        print("="*50)
        print("\nYour PDF generation system is ready to use!")
        print("\nNext steps:")
        print("1. Start the backend: python main.py")
        print("2. Test the endpoint: POST /notes/{note_id}/generate-pdf")
        print("3. Integrate with your frontend")
        return True
    else:
        print("\nIntegration test failed: PDF compilation failed")
        return False


if __name__ == "__main__":
    print("PDF Generation System Test Suite")
    print("="*50)
    
    # Run all tests
    success = test_integration()
    
    if not success:
        print("\nSome tests failed. Please check the error messages above.")
        print("\nCommon issues:")
        print("- OpenAI API key not set (OPENAI_API_KEY)")
        print("- pdflatex not installed (cloud compilation will be used)")
        print("- Network issues (for cloud compilation)")
        sys.exit(1)
    else:
        sys.exit(0)
