import random

class ChichewaIntegrator:
    def __init__(self):
        self.phrases = {
            'greeting': [
                ("Muli bwanji", "How are you?"),
                ("Zikomo", "Greetings/Thank you")
            ],
            'excitement': [
                ("Koma zabwino", "This is great!"),
                ("Zachisangalalo", "Pure happiness!")
            ],
            'success': [
                ("Zachitika", "It's done!"),
                ("Zabwino kwambiri", "Very good!")
            ],
            'closing': [
                ("Tiwonana", "See you later"),
                ("Zikomo kwambiri", "Thank you very much")
            ]
        }
    
    def integrate_phrases(self, content: str, intensity: str = 'subtle') -> str:
        """
        Add appropriate Chichewa phrases to content with context.

        For 'subtle' intensity, it adds a greeting at the beginning
        and a closing at the end.
        """
        if intensity == 'subtle':
            # Select a random greeting and closing
            greeting_ch, greeting_en = random.choice(self.phrases['greeting'])
            closing_ch, closing_en = random.choice(self.phrases['closing'])

            # Format with context
            greeting = f"{greeting_ch} 👋 ({greeting_en})"
            closing = f"{closing_ch} 🙏 ({closing_en})"

            # Add to the content
            content = f"{greeting}\n\n{content}\n\n{closing}"

        # Future placeholder for 'prominent' intensity
        # if intensity == 'prominent':
        #     # Logic to inject phrases throughout the content
        #     pass
            
        return content 