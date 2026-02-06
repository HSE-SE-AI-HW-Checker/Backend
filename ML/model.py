from transformers import GPT2LMHeadModel, GPT2Tokenizer

class Model:
    def __init__(self, model_name: str):
        # TODO: можно попробовать устроить арену слабых моделей
        self.tokenizer = GPT2Tokenizer.from_pretrained(model_name)
        self.model = GPT2LMHeadModel.from_pretrained(model_name)

        self.tokenizer.pad_token = self.tokenizer.eos_token

    def respond(self, prompt: str):
        input_ids = self.tokenizer.encode(prompt, return_tensors='pt')
        
        # Теперь можем передать attention_mask
        attention_mask = (input_ids != self.tokenizer.pad_token_id).long()
        
        output = self.model.generate(
            input_ids, 
            attention_mask=attention_mask,  # Добавляем attention_mask
            max_length=50, 
            num_return_sequences=1, 
            no_repeat_ngram_size=2,
            pad_token_id=self.tokenizer.pad_token_id  # Явно указываем
        )

        return self.tokenizer.decode(output[0], skip_special_tokens=True)
