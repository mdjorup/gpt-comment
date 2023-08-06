import asyncio
import json
from abc import ABC, abstractmethod
from datetime import datetime
from uuid import uuid4

from comments import Comment, QuotedComment
from config import config
from services.ai_service import AIService
from services.firestore_service import FirestoreService
from utils import longest_common_substring

OAI_SERVICE = AIService()


class Essay(ABC):
    def __init__(self, prompt: str, text: str):
        self.prompt: str = prompt.strip()
        self.text = text.strip()
        self.quote_comments: list[QuotedComment] = []
        self.general_comments: list[Comment] = []
        self.processing_costs = 0

    def __len__(self):
        return len(self.text)

    def remove_double_spaces(self):
        while self.text.find("  ") != -1:
            self.text = self.text.replace("  ", " ")

    def get_paragraphs(self) -> list[str]:
        return [
            paragraph.strip()
            for paragraph in self.text.split("\n")
            if paragraph.strip() != ""
        ]

    def character_count(self) -> int:
        return sum([len(paragraph) for paragraph in self.get_paragraphs()])

    def is_multiple_paragraphs(self):
        return len(self.get_paragraphs()) > 1

    def add_unparsed_comments(
        self, unparsed_comments: list[str], quote_comment_delim=" - "
    ):
        for output in unparsed_comments:
            if output.strip() == "":
                continue

            splits = output.split(quote_comment_delim)
            quote = splits[0].strip()
            suggestion = " ".join(splits[1:]).strip()

            lcs = longest_common_substring(quote, self.text).strip()
            if lcs == "":
                continue

            start_index = self.text.find(lcs)
            length = len(lcs)
            new_comment = QuotedComment(suggestion, lcs, start_index, length)
            self.quote_comments.append(new_comment)

    def generate_contraction_comments(self, path_to_contractions_data: str):
        with open(path_to_contractions_data, "r") as f:
            contractions: dict = json.load(f)

        for contraction, correction in contractions.items():
            contr_str = " " + contraction + " "
            correction_str = f"Replace {contraction} with {correction}"

            i = 0
            while self.text.find(contr_str, i) != -1:
                idx = self.text.find(contr_str, i)
                start_index = idx + 1
                length = 1
                new_comment = QuotedComment(
                    correction_str, contraction, start_index, length
                )
                self.quote_comments.append(new_comment)
                i = idx + 1

    def generate_second_person_comments(self, path_to_second_person_data: str):
        with open(path_to_second_person_data, "r") as f:
            second_person: list = json.load(f)

        for word in second_person:
            word_str = " " + word + " "
            correction_str = "Avoid using second person"

            i = 0
            while self.text.find(word_str, i) != -1:
                idx = self.text.find(word_str, i)
                start_index = idx + 1
                length = 1
                new_comment = QuotedComment(correction_str, word, start_index, length)
                self.quote_comments.append(new_comment)
                i = idx + 1

    def add_to_doc(self, document):
        paragraph = document.add_paragraph()
        current_index = 0
        self.quote_comments.sort(key=lambda x: x.start_index)

        for i, comment in enumerate(self.quote_comments):
            start = comment.start_index
            end = min(start + comment.length, len(self.text))
            if i < len(self.quote_comments) - 1:
                end = min(end, self.quote_comments[i + 1].start_index)
                self.quote_comments[i + 1].start_index = max(
                    self.quote_comments[i + 1].start_index, end
                )

            if start > current_index:
                paragraph.add_run(self.text[current_index:start])

            new_run = paragraph.add_run(self.text[start:end])
            if comment.comment != "":
                new_run.add_comment(comment.comment, author="EduAvenues", initials="EA")

            current_index = end

        if current_index < len(self.text):
            paragraph.add_run(self.text[current_index:])

        for comment in self.general_comments:
            document.add_paragraph("\n" + str(comment) + "\n")

        document.add_page_break()

    def upload_result_to_firestore(self):
        instructions = []

        essay_id = str(uuid4())

        instructions.append(
            {
                "path": ["essays", essay_id],
                "data": self.to_dict(),
            }
        )

        for comment in self.general_comments:
            comment_id = str(uuid4())
            instructions.append(
                {
                    "path": ["essays", essay_id, "general_comments", comment_id],
                    "data": comment.to_dict(),
                }
            )

        for comment in self.quote_comments:
            comment_id = str(uuid4())
            instructions.append(
                {
                    "path": ["essays", essay_id, "quoted_comments", comment_id],
                    "data": comment.to_dict(),
                }
            )

        fs = FirestoreService()
        fs.batch_write(instructions)

    @abstractmethod
    def to_dict(self):
        pass

    @abstractmethod
    async def process(self):
        pass


class SPSEssay(Essay):
    def __init__(self, prompt: str, text: str):
        super().__init__(prompt, text)
        self.essay_type = config["spreadsheet"]["sps_start_indicator"]

    async def generate_general_comment(self):
        system_message = f"As a guidance counselor assisting a student with their application essay for a prestigious tech-focused high school, your task is to provide constructive feedback for improvement. Consider the essay question, {self.prompt}, as the foundation for your feedback, ensuring that the recommendations align with the initial prompt. Respond with a compact, yet comprehensive paragraph containing your suggested enhancements."

        completion, cost = await OAI_SERVICE.generate_chat_completion(
            system_message, self.text, "gpt-3.5-turbo", max_tokens=256
        )

        self.processing_costs += cost
        new_comment = Comment(completion, "General Comment:\n")
        self.general_comments.append(new_comment)

    async def generate_grammar_comments(self):
        system_message = f'As an essay guidance counselor, your task is to help a student by identifying grammar mistakes in their writing. Your response should be formatted as a list with each line containing a specific error along with a brief excerpt from the student\'s essay that includes that error. Also provide a succinct suggestion for correcting the mistake.\n\nFor example:\n"want to be a engineer" - Change "a" to "an"\n"I is playing" - incorrect use of "is". Change to "am"'

        paragraphs: list[str] = self.text.split("\n")
        
        async with asyncio.TaskGroup() as tg:
            
            tasks = []
            for paragraph in paragraphs:
                n_errors = max(len(paragraph) // 190, 1)
                task = tg.create_task(OAI_SERVICE.generate_chat_completion(system_message, paragraph, "gpt-3.5-turbo", max_tokens=n_errors * 80))
                tasks.append(task)
              
            for coro in asyncio.as_completed(tasks):
                completion, cost = await coro
                self.processing_costs += cost
                unparsed_comments = completion.split("\n")
                self.add_unparsed_comments(unparsed_comments)


    async def generate_specific_comments(self):
        n_comments = len(self.text) // 225

        system_message = f"You're an essay guidance counselor assisting a student with their TJ application essay. Your key responsibility is to offer constructive suggestions aimed at refining the content and ideas of the essay. Based on the student's essay, generate {n_comments} insightful suggestions, each connected to a specific quote from the text. Format your advice as a list, where each entry begins with a brief quote from the essay, followed by your suggestion for improvement.\nRemember, your goal is to help shape the student's thoughts and arguments, enhancing the overall quality of the essay.\n\n\"Samantha was very angry\" - Try to 'show' the emotions instead of just 'telling'. This will make your narrative more engaging.\n\"I also play tennis\" - Keep your information relevant. Discuss aspects of your background that align with the theme of the essay prompt."
        oai_prompt = f"Essay Prompt:\n{self.prompt}\n\nApplicant's Essay:\n{self.text}"
        completion, cost = await OAI_SERVICE.generate_chat_completion(
            system_message, oai_prompt, "gpt-4", max_tokens=n_comments * 80
        )

        self.processing_costs += cost
        unparsed_comments = completion.split("\n")
        self.add_unparsed_comments(unparsed_comments)

    def to_dict(self) -> dict:
        return {
            "upload_time": datetime.now(),
            "essay_prompt": self.prompt,
            "essay_text": self.text,
            "type": self.essay_type,
            "processing_costs": self.processing_costs,
        }

    async def process(self, progress_bar=None):
        self.remove_double_spaces()
        self.generate_contraction_comments(config["contractions_data_path"])
        self.generate_second_person_comments(config["second_person_data_path"])

        async with asyncio.TaskGroup() as tg:
            tg.create_task(self.generate_grammar_comments())
            tg.create_task(self.generate_specific_comments())
            tg.create_task(self.generate_general_comment())

        try:
            self.upload_result_to_firestore()
        except:
            print("Warning: Failed to upload to Firestore.")

        if progress_bar:
            progress_bar.update(1)


class PSEEssay(Essay):
    def __init__(self, prompt: str, text: str):
        super().__init__(prompt, text)
        self.essay_type = config["spreadsheet"]["pse_start_indicator"]

    async def generate_general_comment(self):
        system_message = f"You're an essay counselor helping a student craft their application essay for TJ, a highly selective technology high school. Assume that your reader possesses a strong mathematical background. The core objective of the essay is to exhibit the student's problem-solving strategies in written form.\nBased on the essay provided, offer your feedback in a succinct paragraph. Your recommendations should aim at enhancing the clarity, specificity, and effectiveness of how the student communicates their problem-solving strategies within the context of the essay."
        oai_prompt = f"Essay Prompt:\n{self.prompt}\n\nApplicant's Essay:\n{self.text}"
        completion, cost = await OAI_SERVICE.generate_chat_completion(
            system_message, oai_prompt, "gpt-3.5-turbo", max_tokens=400
        )
        self.processing_costs += cost
        new_comment = Comment(completion, "General Comment:\n")
        self.general_comments.append(new_comment)

    async def generate_grammar_comments(self):
        n_errors = len(self.text) // 200
        system_message = f'As an essay guidance counselor, your task is to help a student by identifying grammar mistakes in their writing. Your response should be formatted as a list with each line containing a specific error along with a brief excerpt from the student\'s essay that includes that error. Also provide a succinct suggestion for correcting the mistake.\n\nFor example:\n"want to be a engineer" - Change "a" to "an"\n"I is playing" - incorrect use of "is". Change to "am"'

        completion, cost = await OAI_SERVICE.generate_chat_completion(
            system_message, self.text, "gpt-3.5-turbo", max_tokens=n_errors * 80
        )

        self.processing_costs += cost
        unparsed_comments = completion.split("\n")
        self.add_unparsed_comments(unparsed_comments)

    async def generate_specific_comments(self):

        system_message = f'As an essay counselor, your task is to assist a student in articulating their problem-solving process within a written essay. We\'re not focusing on the mathematical accuracy but instead the clarity and flow of the explanation, and the organization of the essay. You should provide recommendations for improving these aspects, without considering the correctness of mathematical logic.\nRespond with a newline-separated list of 5 distinct suggestions for the student, each tied to a specific quote from the text. Your suggestions should aim to enhance the coherence, organization, and clarity of the student\'s explanation\n\nFor example:\n"First, I calculated the sum" - Add more context. What exactly are you summing here and why is it important?\n"This result is impossible" - Suggest: Instead of stating it\'s impossible, explain why it contradicts known principles or assumptions.'

        paragraphs: list[str] = self.text.split("\n")

        async with asyncio.TaskGroup() as tg:
            
            tasks = []
            for paragraph in paragraphs:
                n_errors = max(len(paragraph) // 175, 1)
                task = tg.create_task(OAI_SERVICE.generate_chat_completion(system_message, paragraph, "gpt-4", max_tokens=n_errors * 80, temperature=0.5))
                tasks.append(task)
              
            for coro in asyncio.as_completed(tasks):
                completion, cost = await coro
                self.processing_costs += cost
                unparsed_comments = completion.split("\n")
                self.add_unparsed_comments(unparsed_comments)

    def to_dict(self) -> dict:
        return {
            "upload_time": datetime.now(),
            "essay_prompt": self.prompt,
            "essay_text": self.text,
            "type": self.essay_type,
            "processing_costs": self.processing_costs,
        }

    async def process(self, progress_bar=None):
        self.remove_double_spaces()
        self.generate_contraction_comments(config["contractions_data_path"])
        self.generate_second_person_comments(config["second_person_data_path"])

        async with asyncio.TaskGroup() as tg:
            tg.create_task(self.generate_general_comment())
            # tg.create_task(self.generate_grammar_comments()) # not sure if we want these. Going to leave them out.
            tg.create_task(self.generate_specific_comments())

        try:
            self.upload_result_to_firestore()
        except:
            print("Warning: Failed to upload to Firestore.")

        if progress_bar:
            progress_bar.update(1)
