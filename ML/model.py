from transformers import GPT2LMHeadModel, GPT2Tokenizer

class Model:
    def __init__(self, model_name: str):
        # TODO: можно попробовать устроить арену слабых моделей
        self.tokenizer = GPT2Tokenizer.from_pretrained(model_name)
        self.model = GPT2LMHeadModel.from_pretrained(model_name)

    def responde(self, prompt: str):
        input_ids = self.tokenizer.encode(prompt, return_tensors='pt')
        output = self.model.generate(input_ids, max_length=50, num_return_sequences=1, no_repeat_ngram_size=2)
        return self.tokenizer.decode(output[0], skip_special_tokens=True)
