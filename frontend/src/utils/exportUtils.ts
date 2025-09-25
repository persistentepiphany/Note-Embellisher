// Utility functions for exporting and downloading files

export const downloadTextFile = (content: string, filename: string = 'notes.txt') => {
  const blob = new Blob([content], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};

export const exportToPDF = async (content: string, title: string = 'Enhanced Notes') => {
  try {
    // Dynamic import of jsPDF to avoid bundling issues
    const { jsPDF } = await import('jspdf');
    
    const doc = new jsPDF();
    
    // Set title
    doc.setFontSize(16);
    doc.setFont('helvetica', 'bold');
    doc.text(title, 20, 20);
    
    // Add timestamp
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    const timestamp = new Date().toLocaleString();
    doc.text(`Generated on: ${timestamp}`, 20, 30);
    
    // Add content
    doc.setFontSize(12);
    doc.setFont('helvetica', 'normal');
    
    // Split content into lines that fit the page width
    const pageWidth = doc.internal.pageSize.getWidth();
    const margin = 20;
    const maxWidth = pageWidth - 2 * margin;
    
    const lines = doc.splitTextToSize(content, maxWidth);
    
    let yPosition = 45;
    const lineHeight = 7;
    const pageHeight = doc.internal.pageSize.getHeight();
    
    lines.forEach((line: string) => {
      if (yPosition > pageHeight - margin) {
        doc.addPage();
        yPosition = margin;
      }
      doc.text(line, margin, yPosition);
      yPosition += lineHeight;
    });
    
    // Save the PDF
    const filename = `${title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_${Date.now()}.pdf`;
    doc.save(filename);
    
    return true;
  } catch (error) {
    console.error('Error generating PDF:', error);
    throw new Error('Failed to generate PDF. Please try again.');
  }
};

export const exportToWord = (content: string, title: string = 'Enhanced Notes') => {
  // Create a simple HTML document structure for Word compatibility
  const htmlContent = `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>${title}</title>
      <style>
        body { font-family: Arial, sans-serif; margin: 1in; line-height: 1.6; }
        h1 { color: #333; border-bottom: 2px solid #333; padding-bottom: 10px; }
        .timestamp { color: #666; font-size: 0.9em; margin-bottom: 20px; }
        .content { white-space: pre-wrap; }
      </style>
    </head>
    <body>
      <h1>${title}</h1>
      <div class="timestamp">Generated on: ${new Date().toLocaleString()}</div>
      <div class="content">${content.replace(/\n/g, '<br>')}</div>
    </body>
    </html>
  `;
  
  const blob = new Blob([htmlContent], { type: 'application/msword' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_${Date.now()}.doc`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};