import os
import re
from pypdf import PdfReader


class PDFService:

    def get_all_papers(self, dataset_path):
        papers = []

        for reviewer in os.listdir(dataset_path):

            reviewer_path = os.path.join(
                dataset_path,
                reviewer
            )

            if not os.path.isdir(reviewer_path):
                continue

            for file in os.listdir(reviewer_path):

                if file.lower().endswith(".pdf"):

                    papers.append({
                        "reviewer": reviewer,
                        "filename": file,
                        "filepath": os.path.join(
                            reviewer_path,
                            file
                        )
                    })

        return papers

    # --------------------------------------------------
    # EXTRACT FULL TEXT
    # --------------------------------------------------

    def extract_text(self, filepath):
        """
        Extract text from a PDF and clean it.
        """

        reader = PdfReader(filepath)

        pages = []

        for page in reader.pages:

            text = page.extract_text()

            if text:
                pages.append(text)

        text = "\n".join(pages)

        return self.clean_text(text)

    # --------------------------------------------------
    # CLEAN TEXT
    # --------------------------------------------------

    def clean_text(self, text):
        """
        Clean common PDF extraction problems.
        """

        # Fix words broken across lines
        # Example:
        # cardio-
        # protection
        # ->
        # cardioprotection

        text = re.sub(
            r"(\w)-\s*\n\s*(\w)",
            r"\1\2",
            text
        )

        # Replace tabs and multiple spaces
        text = re.sub(
            r"[ \t]+",
            " ",
            text
        )

        # Remove spaces around newlines
        text = re.sub(
            r" *\n *",
            "\n",
            text
        )

        # Remove excessive blank lines
        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text
        )

        return text.strip()

    # --------------------------------------------------
    # EXTRACT PAPER INFORMATION
    # --------------------------------------------------

    def extract_paper_info(self, filepath):
        """
        Extract title, abstract and keywords.
        """

        text = self.extract_text(filepath)

        title = self.extract_title(text)

        abstract = self.extract_abstract(text)

        keywords = self.extract_keywords(text)

        return {
            "title": title,
            "abstract": abstract,
            "keywords": keywords
        }

    # --------------------------------------------------
    # TITLE
    # --------------------------------------------------

    def extract_title(self, text):
        """
        Extract the research paper title.
        """

        lines = [
            line.strip()
            for line in text.split("\n")
            if line.strip()
        ]

        if not lines:
            return ""

        # Find Abstract
        abstract_index = None

        for i, line in enumerate(lines):

            if re.fullmatch(
                r"abstract",
                line,
                re.IGNORECASE
            ):
                abstract_index = i
                break

        if abstract_index is None:
            abstract_index = min(
                len(lines),
                30
            )

        candidates = []

        for i, line in enumerate(
            lines[:abstract_index]
        ):

            lower = line.lower()

            # Ignore page numbers
            if line.isdigit():
                continue

            # Ignore journal information
            if re.search(
                r"\b\d+\s*:\s*\d+[-–]\d+,\s*\d{4}\b",
                line
            ):
                continue

            # Ignore copyright
            if "©" in line:
                continue

            if "kluwer academic" in lower:
                continue

            # Ignore affiliations
            if self.is_affiliation(line):
                continue

            # Ignore author lines
            if self.looks_like_authors(line):
                continue

            # Ignore received / accepted information
            if lower.startswith("received"):
                continue

            if lower.startswith("accepted"):
                continue

            # Ignore very short lines
            if len(line) < 10:
                continue

            # Ignore very long lines
            if len(line) > 200:
                continue

            candidates.append(
                (i, line)
            )

        if not candidates:
            return ""

        # Title is normally the first
        # continuous meaningful block.

        title_lines = []

        previous_index = None

        for index, line in candidates:

            if (
                previous_index is not None
                and index != previous_index + 1
            ):
                break

            title_lines.append(line)

            previous_index = index

        return " ".join(title_lines).strip()

    # --------------------------------------------------
    # AUTHOR DETECTION
    # --------------------------------------------------

    def looks_like_authors(self, line):
        """
        Detect lines that probably contain author names.
        """

        if "," not in line:
            return False

        parts = [
            part.strip()
            for part in line.split(",")
            if part.strip()
        ]

        if len(parts) < 2:
            return False

        name_like = 0

        for part in parts:

            words = part.split()

            if 2 <= len(words) <= 5:
                name_like += 1

        return name_like >= 2

    # --------------------------------------------------
    # AFFILIATION DETECTION
    # --------------------------------------------------

    def is_affiliation(self, line):
        """
        Detect common author affiliation lines.
        """

        lower = line.lower()

        affiliation_words = [
            "department",
            "university",
            "institute",
            "school",
            "centre",
            "center",
            "college",
            "hospital",
            "laboratory",
            "laboratories",
            "faculty",
            "division",
            "research",
            "academy"
        ]

        if any(
            word in lower
            for word in affiliation_words
        ):
            return True

        # Email
        if "@" in line:
            return True

        return False

    # --------------------------------------------------
    # ABSTRACT
    # --------------------------------------------------

    def extract_abstract(self, text):
        """
        Extract the abstract section.
        """

        abstract_match = re.search(
            r"(?i)\babstract\b",
            text
        )

        if not abstract_match:
            return ""

        start = abstract_match.end()

        # Possible end of abstract
        end_patterns = [
            r"(?i)\bkeywords?\s*:",
            r"(?i)\bkey\s*words?\s*:",
            r"(?i)\b1\.?\s+introduction\b",
            r"(?i)\bintroduction\b"
        ]

        end_positions = []

        for pattern in end_patterns:

            match = re.search(
                pattern,
                text[start:]
            )

            if match:

                end_positions.append(
                    start + match.start()
                )

        if end_positions:
            end = min(end_positions)
        else:
            end = len(text)

        abstract = text[start:end]

        return self.clean_section(
            abstract
        )

    # --------------------------------------------------
    # KEYWORDS
    # --------------------------------------------------

    def extract_keywords(self, text):
        """
        Extract keywords from the paper.
        """

        # Find Keywords: or Key words:
        match = re.search(
            r"(?is)\bkey\s*words?\s*:\s*(.*)",
            text
        )

        if not match:
            return []

        keyword_text = match.group(1)

        # Stop at the beginning of Introduction
        stop_patterns = [
            r"\n\s*1\.?\s+introduction\b",
            r"\n\s*introduction\b",
            r"\n\s*1\s+"
        ]

        end_positions = []

        for pattern in stop_patterns:

            stop = re.search(
                pattern,
                keyword_text,
                re.IGNORECASE
            )

            if stop:

                end_positions.append(
                    stop.start()
                )

        if end_positions:

            keyword_text = keyword_text[
                :min(end_positions)
            ]

        # Clean whitespace
        keyword_text = self.clean_section(
            keyword_text
        )

        # Split by comma or semicolon
        keywords = re.split(
            r",|;",
            keyword_text
        )

        keywords = [
            keyword.strip()
            for keyword in keywords
            if keyword.strip()
        ]

        return keywords

    # --------------------------------------------------
    # CLEAN SECTION
    # --------------------------------------------------

    def clean_section(self, text):
        """
        Clean extracted sections.
        """

        # Fix broken words
        text = re.sub(
            r"(\w)-\s*\n\s*(\w)",
            r"\1\2",
            text
        )

        # Replace newlines and multiple spaces
        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text.strip()