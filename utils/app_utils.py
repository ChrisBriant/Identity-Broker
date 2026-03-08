import random

def create_random_username():
  with open('./words_max_length_six.txt', 'r') as f:
    lines = f.readlines()

  random_words = random.sample(lines, 3)
  random_words = [word.strip().capitalize() for word in random_words]
  print(random_words)
  return "".join(random_words)
