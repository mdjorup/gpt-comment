import asyncio
import json
from abc import ABC, abstractmethod

from comments import Comment, QuotedComment
from config import config
from services.ai_service import AIService
from utils import longest_common_substring

gpt_model : str = config["gpt_model_id"]


class Essay(ABC):

    def __init__(self, prompt: str, text: str):
        self.prompt : str = prompt.strip()
        self.text = text.strip()
        self.quote_comments : list[QuotedComment]= []
        self.general_comments : list[Comment] = []
        self.processing_costs = 0


    def __len__(self):
        return len(self.text)

    
    def remove_double_spaces(self):
        while self.text.find("  ") != -1:
            self.text = self.text.replace("  ", " ")
    

    def get_paragraphs(self) -> list[str]:
        return [paragraph.strip() for paragraph in self.text.split("\n") if paragraph.strip() != ""]
    

    def character_count(self) -> int:
        return sum([len(paragraph) for paragraph in self.get_paragraphs()])
    

    def is_multiple_paragraphs(self):
        return len(self.get_paragraphs()) > 1
    
    def add_unparsed_comments(self, unparsed_comments : list[str], quote_comment_delim = " - "):
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

    def generate_contraction_comments(self, path_to_contractions_data : str):
        with open(path_to_contractions_data, "r") as f:
            contractions : dict = json.load(f)

        for contraction, correction in contractions.items():
            contr_str = " " + contraction + " "
            correction_str = f"Replace {contraction} with {correction}"
            
            i = 0
            while self.text.find(contr_str, i) != -1:
                idx = self.text.find(contr_str, i)                
                start_index = idx + 1
                length = 1
                new_comment = QuotedComment(correction_str, contraction, start_index, length)
                self.quote_comments.append(new_comment)
                i = idx + 1

    
    def generate_second_person_comments(self, path_to_second_person_data : str):
        with open(path_to_second_person_data, "r") as f:
            second_person : list = json.load(f)
        
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
                end = min(end, self.quote_comments[i+1].start_index)
                self.quote_comments[i+1].start_index = max(self.quote_comments[i+1].start_index, end)
            
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


    @abstractmethod
    async def process(self):
        pass

    



class SPSEssay(Essay):

    def __init__(self, prompt: str, text: str):
        super().__init__(prompt, text)
        self.essay_type = config["spreadsheet"]["sps_start_indicator"]
        

    async def generate_general_comment(self):
        system_message = f"You are an essay counselor helping a student write a better essay for their application to a selective technology high school. Respond with a short paragraph recommending improvements to the essay based on the following prompt:\n{self.prompt}"
        
        oai = AIService()
        completion, cost = await oai.generate_chat_completion(system_message, self.text, gpt_model, max_tokens=256)

        self.processing_costs += cost
        new_comment = Comment(completion, "General Comment:\n")
        self.general_comments.append(new_comment)

    
    async def generate_grammar_comments(self):
        n_errors = len(self.text) // 200

        system_message = f'You are an essay counselor helping a student. Respond with a newline separated list of {n_errors} grammar errors and a short suggestion directed at the student to fix the error, where each error is attached to a concise quote from the text.\n\nExample:\n"want to be a engineer" - Change "a" to "an"\n"I is playing" - incorrect use of "is". Change to "am"'

        oai = AIService()
        completion, cost = await oai.generate_chat_completion(system_message, self.text, gpt_model, max_tokens=n_errors*80)

        self.processing_costs += cost
        unparsed_comments = completion.split("\n")
        self.add_unparsed_comments(unparsed_comments)


    async def generate_specific_comments(self):
        n_comments = len(self.text) // 250
        system_message = f'You are an essay counselor helping a student write their application to TJ. Respond with a newline separated list of {n_comments} short suggestions directed at the student, where each suggestion is attached to a concise quote from the text.\n\nExample:\n"Samantha was very angry" - Remember to show, do not tell\n"I also play tennis" - Make sure to focus on relevant parts of your background and the prompt.'

        oai_prompt = f'Prompt:\n{self.prompt}\n\nEssay:\n{self.text}'
        oai = AIService()
        completion, cost = await oai.generate_chat_completion(system_message, oai_prompt, gpt_model, max_tokens=n_comments*80)

        self.processing_costs += cost
        unparsed_comments = completion.split("\n")
        self.add_unparsed_comments(unparsed_comments)


    async def process(self, progress_bar = None):
        self.remove_double_spaces()
        self.generate_contraction_comments(config["contractions_data_path"])
        self.generate_second_person_comments(config["second_person_data_path"])
        

        async with asyncio.TaskGroup() as tg:
            tg.create_task(self.generate_grammar_comments())
            tg.create_task(self.generate_specific_comments())
            tg.create_task(self.generate_general_comment())

        if progress_bar:
            progress_bar.update(1)
        

 

class PSEEssay(Essay):

    def __init__(self, prompt: str, text: str):
        super().__init__(prompt, text)
        self.essay_type = config["spreadsheet"]["pse_start_indicator"]


    async def generate_general_comment(self):
        system_message = f"You are a essay counselor helping a student apply to a selective technology high school called TJ. Assume the reader has a strong math background. The goal is to highlight the student's problem solving strategies through writing.\n\nRespond with a short paragraph recommending improvements to the essay based on the goal."
        oai_prompt = f'Prompt:\n{self.prompt}\n\nEssay:\n{self.text}'
        oai = AIService()
        completion, cost = await oai.generate_chat_completion(system_message, oai_prompt, gpt_model, max_tokens=400)
        self.processing_costs += cost
        new_comment = Comment(completion, "General Comment:\n")
        self.general_comments.append(new_comment)

    async def generate_grammar_comments(self):
        n_errors = len(self.text) // 200
        system_message = f'You are an essay counselor helping a student. Respond with a newline separated list of {n_errors} grammar errors and a short suggestion directed at the student to fix the error, where each error is attached to a concise quote from the text.\n\nExample:\n"want to be a engineer" - Change "a" to "an"\n"I is playing" - incorrect use of "is". Change to "am"'

        oai = AIService()
        completion, cost = await oai.generate_chat_completion(system_message, self.text, gpt_model, max_tokens=n_errors*80)

        self.processing_costs += cost
        unparsed_comments = completion.split("\n")
        self.add_unparsed_comments(unparsed_comments)

    async def generate_specific_comments(self):
        n_comments = len(self.text) // 250
        system_message = f'You are a essay counselor helping a student apply to a selective technology high school called TJ. Assume the reader has a strong math background. Respond with a newline separated list of {n_comments} short suggestions directed at the student, where each suggestion is attached to a concise quote from the text. Focus on the problem-solving process.\n\nExample:\n"The answers previously stated are theoretical" - Make sure to include assumptions made in this experiment.\n"25% + 50% + 10% = 80%" - This calculation may be incorrect. Double check your math'

        oai_prompt = f'Prompt:\n{self.prompt}\n\nEssay:\n{self.text}'
        oai = AIService()
        completion, cost = await oai.generate_chat_completion(system_message, oai_prompt, gpt_model, max_tokens=n_comments*80)

        self.processing_costs += cost
        unparsed_comments = completion.split("\n")
        self.add_unparsed_comments(unparsed_comments)


    async def process(self, progress_bar=None):
        self.remove_double_spaces()
        self.generate_contraction_comments(config["contractions_data_path"])
        self.generate_second_person_comments(config["second_person_data_path"])

        async with asyncio.TaskGroup() as tg:
            tg.create_task(self.generate_general_comment())
            tg.create_task(self.generate_grammar_comments())
            tg.create_task(self.generate_specific_comments())

        if progress_bar:
            progress_bar.update(1)

        



    