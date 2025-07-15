\# PDF Quiz Extractor



A web-based quiz application that extracts questions, options, and answers from PDF files and presents them in an interactive timed quiz format.



\## 🚀 Features



\- 📄 \*\*PDF Parsing\*\*: Automatically extracts questions and answers from PDF files

\- ⏱️ \*\*Timed Questions\*\*: Configurable time limits for each question

\- 🎯 \*\*Interactive Interface\*\*: Modern web-based quiz interface

\- 📊 \*\*Detailed Results\*\*: Comprehensive performance analysis with explanations

\- 🖼️ \*\*Image Support\*\*: Extracts and displays images from PDFs

\- 💾 \*\*Session Management\*\*: Maintains quiz state across pages



\## 📋 Requirements



\- Python 3.7+

\- Flask

\- PyPDF2

\- PyMuPDF

\- Pillow

\- pdfplumber



\## 🛠️ Installation



1\. \*\*Clone the repository\*\*

&nbsp;  ```bash

&nbsp;  git clone https://github.com/yourusername/pdf-quiz-extractor.git

&nbsp;  cd pdf-quiz-extractor

&nbsp;  ```



2\. \*\*Create virtual environment\*\*

&nbsp;  ```bash

&nbsp;  python -m venv venv

&nbsp;  venv\\Scripts\\activate  # On Windows

&nbsp;  source venv/bin/activate  # On macOS/Linux

&nbsp;  ```



3\. \*\*Install dependencies\*\*

&nbsp;  ```bash

&nbsp;  pip install -r requirements.txt

&nbsp;  ```



4\. \*\*Run the application\*\*

&nbsp;  ```bash

&nbsp;  python app.py

&nbsp;  ```



5\. \*\*Open browser and go to\*\* `http://localhost:5000`



\## 📖 Usage



\### PDF Format Requirements

Your PDF should have questions in this format:

```

Q1. What is the capital of France?

A. London

B. Berlin

C. Paris

D. Madrid

Answer: Option C

Explanation: Paris is the capital of France.

```



\### How to Use

1\. Start the application

2\. Upload or specify path to your PDF file

3\. Set time limit per question

4\. Take the quiz

5\. View detailed results and explanations



\## 🎯 Supported PDF Formats

\- Questions: Q1., Q2., Q3., etc.

\- Options: A., B., C., D.

\- Answers: "Answer: Option X" or "Answer: X"

\- Explanations: "Explanation: ..." (optional)



\## 🌐 Live Demo

\[Add your deployed app URL here]



\## 📸 Screenshots



!\[Home Page](screenshots/home.png)

!\[Quiz Interface](screenshots/quiz.png)

!\[Results Page](screenshots/results.png)



\## 🤝 Contributing



1\. Fork the repository

2\. Create a feature branch (`git checkout -b feature/amazing-feature`)

3\. Commit your changes (`git commit -m 'Add amazing feature'`)

4\. Push to the branch (`git push origin feature/amazing-feature`)

5\. Open a Pull Request



\## 📄 License



This project is licensed under the MIT License - see the LICENSE file for details.



\## 👨‍💻 Author



Created by \[Your Name]



\## 🐛 Issues



If you encounter any issues, please create an issue on GitHub.

```





