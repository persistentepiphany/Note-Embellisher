"""
LaTeX Generation Service
Converts any note content into well-formatted LaTeX documents using OpenAI
OpenAI handles all formatting decisions - works for any subject (math, science, humanities, etc.)
"""
import os
from typing import List, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class LaTeXService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        
        if not self.api_key:
            print("WARNING: OPENAI_API_KEY not found - LaTeX generation will use fallback")
            return
        
        try:
            self.client = OpenAI(api_key=self.api_key)
            print("LaTeX Service initialized with OpenAI")
        except Exception as e:
            print(f"Failed to initialize OpenAI for LaTeX: {e}")
            self.client = None
    
    def _strip_pagebreak_tokens(self, content: str) -> str:
        """
        Strip or convert page-break tokens that are rendered by jsPDF but not valid for LaTeX.
        These markers (###, ##, #, %P%P%P) are jsPDF-specific and need to be removed or converted.
        
        Args:
            content: The text content with potential page-break markers
            
        Returns:
            Content with markers stripped or converted to LaTeX equivalents
        """
        import re
        
        # Remove %P%P%P page-break tokens entirely
        content = content.replace('%P%P%P', '')
        
        # Convert markdown headers (###, ##, #) to nothing - let OpenAI decide structure
        # OR keep them as they might be meaningful headers, not page breaks
        # Based on instructions, we should strip them if they're being used as raw page breaks
        # Let's be conservative and only strip if they appear to be standalone
        
        # Remove standalone # markers that appear to be page breaks (not markdown headers)
        content = re.sub(r'\n#{1,3}\s*\n', '\n\n', content)  # Remove # lines with nothing else
        
        # Clean up multiple consecutive newlines
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        return content.strip()
    
    def generate_latex_document(
        self, 
        content: str,
        title: Optional[str] = None,
        author: Optional[str] = None,
        style: str = "academic",
        font: str = "Times New Roman"
    ) -> str:
        """
        Generate a complete, well-formatted LaTeX document from any note content.
        OpenAI intelligently determines the subject matter and formats appropriately.
        
        Args:
            content: The note content (already processed/enhanced by ChatGPT)
            title: Optional document title
            author: Optional author name
            
        Returns:
            Complete LaTeX document as string ready for compilation
        """
        # Strip jsPDF page-break tokens that are rendered by jsPDF client-side
        content = self._strip_pagebreak_tokens(content)
        
        print(f"DEBUG: Content after stripping page-break tokens: {len(content)} chars")
        print(f"DEBUG: First 200 chars: {content[:200]}")
        print(f"DEBUG: Last 200 chars: {content[-200:]}")
        
        if not self.client:
            print("OpenAI client not available, using basic LaTeX template")
            return self._generate_basic_latex(content, title, author, style, font)
        
        try:
            # Let OpenAI do ALL the work - it will determine subject, format math, create structure
            prompt = self._create_latex_conversion_prompt(content, title, author, style, font)
            
            print(f"Calling OpenAI API for LaTeX generation (content length: {len(content)} chars)...")
            print(f"Prompt length: {len(prompt)} chars")
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert LaTeX document formatter. Convert any note content into a "
                            "complete, professional LaTeX document. Automatically detect the subject matter "
                            "(math, science, humanities, etc.) and format appropriately. Use proper LaTeX "
                            "environments, mathematical notation, section hierarchy, and professional typography. "
                            "CRITICAL: You MUST complete the entire document. Output the FULL LaTeX code from "
                            "\\documentclass to \\end{document}. Do NOT truncate. Output ONLY valid LaTeX code - "
                            "no explanations, no markdown blocks, no code fences."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=16000  # Increased from 4000 to allow longer documents
            )
            
            latex_content = response.choices[0].message.content.strip()
            print(f"OpenAI returned {len(latex_content)} chars of LaTeX")
            
            # Check if response was truncated
            if response.choices[0].finish_reason == "length":
                print("WARNING: OpenAI response was truncated due to token limit!")
                print("The document may be incomplete. Consider shortening the input content.")
            
            # Check if response was truncated
            if response.choices[0].finish_reason == "length":
                print("WARNING: OpenAI response was truncated due to token limit!")
                print("The document may be incomplete. Consider shortening the input content.")
            
            # Clean up any markdown code blocks if present
            if latex_content.startswith("```"):
                print("Removing markdown code fence from OpenAI response...")
                lines = latex_content.split('\n')
                # Remove first line (```latex or ```) and last line (```)
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                latex_content = '\n'.join(lines)
            
            # Ensure document ends properly
            if not latex_content.strip().endswith("\\end{document}"):
                print("WARNING: LaTeX document doesn't end with \\end{document}, adding it...")
                latex_content = latex_content.rstrip() + "\n\n\\end{document}"
            
            # Ensure proper document structure
            if not latex_content.startswith("\\documentclass"):
                print("OpenAI didn't return full document, wrapping content...")
                latex_content = self._wrap_in_document_structure(latex_content, title, author)

            latex_content = self._ensure_theorem_environments(latex_content)
            
            print("LaTeX document generated successfully with OpenAI")
            print(f"Final LaTeX length: {len(latex_content)} chars")
            return latex_content
            
        except Exception as e:
            print(f"ERROR: OpenAI LaTeX generation failed: {e}")
            print("Using fallback LaTeX generation...")
            import traceback
            traceback.print_exc()
            return self._generate_basic_latex(content, title, author, style, font)
    
    def _create_latex_conversion_prompt(
        self, 
        content: str,
        title: Optional[str],
        author: Optional[str],
        style: str,
        font: str
    ) -> str:
        """Create a detailed prompt for OpenAI to generate LaTeX from any content"""
        
        title_text = title if title else "Notes"
        author_text = author if author else "Student"

        style_profiles = {
            "academic": (
                "Adopt a scholarly, publication-ready layout with clear hierarchy, theorem/definition"
                " environments when applicable, and refined spacing suitable for research notes."
            ),
            "personal": (
                "Use a friendly tone suited for personal study notes with callouts, softer color accents,"
                " and relaxed spacing that remains organized."
            ),
            "minimalist": (
                "Keep the layout extremely clean with minimalist headings, generous whitespace, and"
                " only essential decorative elements."
            )
        }
        normalized_style = (style or "academic").lower()
        style_instruction = style_profiles.get(normalized_style, style_profiles["academic"])
        font_choice = font or "Times New Roman"
        font_instruction = (
            f"Typography preference: match the '{font_choice}' family using appropriate LaTeX packages"
            " (e.g., fontspec, mathptmx, helvet) so the entire document keeps consistent type."
        )
        
        prompt = f"""Convert the following note content into a complete, professional LaTeX document.

REQUIREMENTS:
1. Start with \\documentclass[12pt,a4paper]{{article}}
2. Include appropriate packages based on content needs:
   - amsmath, amssymb, amsthm (for any mathematical content)
   - graphicx, hyperref (standard)
   - fancyhdr (for headers/footers)
   - geometry (for margins)
   - Any other packages needed for the content
3. Set document title: {title_text}
4. Set author: {author_text}
5. Use \\maketitle
6. Style direction: {style_instruction}
7. {font_instruction}

FORMATTING INSTRUCTIONS:
- Automatically detect the subject matter from the content
- Create appropriate section hierarchy (\\section, \\subsection, etc.)
- If content contains math, use proper LaTeX math notation ($...$, $$...$$, \\[...\\])
- Use theorem environments (theorem, lemma, definition) if content is mathematical
- For lists, use itemize or enumerate
- Add emphasis with \\textbf{{}}, \\textit{{}} where appropriate
- Include \\tableofcontents if content is substantial (multiple sections)
- Use proper spacing and paragraph breaks
- Set margins: \\usepackage[margin=1in]{{geometry}}

CONTENT TO CONVERT:
{content}

OUTPUT: Complete LaTeX document starting with \\documentclass and ending with \\end{{document}}.
Output ONLY the LaTeX code - no explanations, no markdown code blocks."""

        return prompt
    
    def _wrap_in_document_structure(
        self, 
        latex_body: str, 
        title: Optional[str],
        author: Optional[str]
    ) -> str:
        """Wrap LaTeX content in proper document structure if OpenAI didn't provide it"""
        
        title_text = title if title else "Notes"
        author_text = author if author else "Student"
        
        latex_doc = r"""\documentclass[12pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage{amsmath,amssymb,amsthm}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage{fancyhdr}
\usepackage[margin=1in]{geometry}

\pagestyle{fancy}
\fancyhf{}
\rhead{""" + title_text + r"""}
\cfoot{\thepage}

\newtheorem{theorem}{Theorem}
\newtheorem{lemma}[theorem]{Lemma}
\newtheorem{definition}{Definition}
\newtheorem{corollary}{Corollary}

\title{""" + title_text + r"""}
\author{""" + author_text + r"""}
\date{\today}

\begin{document}
\maketitle

""" + latex_body + r"""

\end{document}
"""
        
        return latex_doc

    def _ensure_theorem_environments(self, latex_content: str) -> str:
        """Insert default theorem/lemma/definition declarations when missing."""
        env_declarations = {
            "theorem": r"\newtheorem{theorem}{Theorem}",
            "lemma": r"\newtheorem{lemma}[theorem]{Lemma}",
            "definition": r"\newtheorem{definition}{Definition}",
            "corollary": r"\newtheorem{corollary}{Corollary}"
        }

        needed: List[str] = []
        for env, declaration in env_declarations.items():
            if f"\\begin{{{env}}}" in latex_content and declaration not in latex_content:
                needed.append(declaration)

        if not needed:
            return latex_content

        insertion_block = "\n" + "\n".join(needed) + "\n"
        insert_at = latex_content.find("\\begin{document}")
        if insert_at == -1:
            print("WARNING: Couldn't find \\\"\\begin{document}\\\" when inserting theorem declarations.")
            return insertion_block + latex_content

        before = latex_content[:insert_at]
        after = latex_content[insert_at:]
        print("Injecting missing theorem environment declarations into LaTeX preamble")
        return before + insertion_block + after
    
    def _generate_basic_latex(
        self, 
        content: str,
        title: Optional[str],
        author: Optional[str],
        style: str,
        font: str
    ) -> str:
        """Generate basic LaTeX document without AI enhancement (fallback)"""
        
        print("WARNING: Using basic LaTeX fallback (no AI enhancement)")
        
        title_text = title if title else "Notes"
        author_text = author if author else "Student"
        normalized_style = (style or "academic").lower()
        
        # Convert markdown to basic LaTeX instead of just escaping
        latex_body = self._markdown_to_basic_latex(content)
        font_block = self._font_package_for_name(font)
        style_block = self._style_customization_block(normalized_style)
        extras: List[str] = []
        for block in (font_block, style_block):
            if block:
                extras.extend(block.strip().splitlines())
        
        preamble_lines = [
            r"\documentclass[12pt,a4paper]{article}",
            r"\usepackage[utf8]{inputenc}",
            r"\usepackage{amsmath,amssymb,amsthm}",
            r"\usepackage{graphicx}",
            r"\usepackage{hyperref}",
            r"\usepackage{fancyhdr}",
            r"\usepackage[margin=1in]{geometry}",
        ]
        preamble_lines.extend(extras)
        preamble_lines.extend([
            "",
            r"\pagestyle{fancy}",
            r"\fancyhf{}",
            rf"\rhead{{{title_text}}}",
            r"\cfoot{\thepage}",
            "",
            r"\newtheorem{theorem}{Theorem}",
            r"\newtheorem{lemma}[theorem]{Lemma}",
            r"\newtheorem{definition}{Definition}",
            "",
            rf"\title{{{title_text}}}",
            rf"\author{{{author_text}}}",
            r"\date{\today}",
            "",
            r"\begin{document}",
            r"\maketitle",
            "",
        ])
        preamble = "\n".join(preamble_lines)
        latex_doc = preamble + latex_body + "\n\n\\end{document}\n"
        
        return latex_doc

    def _font_package_for_name(self, font: Optional[str]) -> str:
        """Map friendly font names to LaTeX package directives."""
        if not font:
            font = "Times New Roman"
        normalized = font.lower()
        if "helvetica" in normalized or "arial" in normalized:
            return "\\usepackage[scaled]{helvet}\n\\renewcommand\\familydefault{\\sfdefault}\n"
        if "palatino" in normalized:
            return "\\usepackage{mathpazo}\n"
        if "garamond" in normalized:
            return "\\usepackage{garamondx}\n"
        if "monospace" in normalized or "mono" in normalized:
            return "\\renewcommand{\\familydefault}{\\ttdefault}\n"
        # Default serif similar to Times
        return "\\usepackage{mathptmx}\n"

    def _style_customization_block(self, style: str) -> str:
        """Return small LaTeX tweaks that mimic the requested style."""
        normalized = (style or "academic").lower()
        styles = {
            "academic": "\\linespread{1.1}\n\\setlength{\\parindent}{15pt}\n",
            "personal": "\\setlength{\\parindent}{10pt}\n\\setlength{\\parskip}{8pt}\n",
            "minimalist": "\\setlength{\\parindent}{0pt}\n\\setlength{\\parskip}{10pt}\n"
        }
        return styles.get(normalized, styles["academic"])
    
    def _markdown_to_basic_latex(self, text: str) -> str:
        """Convert basic markdown to LaTeX (simple conversion for fallback)"""
        import re
        
        lines = text.split('\n')
        latex_lines = []
        
        for line in lines:
            # Convert headers
            if line.startswith('# '):
                latex_lines.append('\\section{' + line[2:].strip() + '}')
            elif line.startswith('## '):
                latex_lines.append('\\subsection{' + line[3:].strip() + '}')
            elif line.startswith('### '):
                latex_lines.append('\\subsubsection{' + line[4:].strip() + '}')
            # Convert bold
            elif '**' in line:
                line = re.sub(r'\*\*(.*?)\*\*', r'\\textbf{\1}', line)
                latex_lines.append(line)
            # Convert italic
            elif '*' in line or '_' in line:
                line = re.sub(r'\*(.*?)\*', r'\\textit{\1}', line)
                line = re.sub(r'_(.*?)_', r'\\textit{\1}', line)
                latex_lines.append(line)
            # Keep other lines as-is (with basic escaping for special chars only when needed)
            else:
                # Only escape truly dangerous LaTeX chars, not content
                safe_line = line.replace('\\', '\\textbackslash{}')
                safe_line = safe_line.replace('{', '\\{').replace('}', '\\}')
                safe_line = safe_line.replace('$', '\\$')
                latex_lines.append(safe_line)
        
        return '\n'.join(latex_lines)
    
    def _escape_latex_chars(self, text: str) -> str:
        """Escape special LaTeX characters in plain text"""
        replacements = {
            '\\': r'\textbackslash{}',
            '&': r'\&',
            '%': r'\%',
            '$': r'\$',
            '#': r'\#',
            '_': r'\_',
            '{': r'\{',
            '}': r'\}',
            '~': r'\textasciitilde{}',
            '^': r'\textasciicircum{}',
        }
        
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        
        return text


# Create singleton instance
latex_service = LaTeXService()
