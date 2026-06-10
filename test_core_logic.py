import sys
import os
import re
from typing import Any
from unittest.mock import MagicMock

# Add lib to path
sys.path.append(os.path.join(os.getcwd(), "lib"))

# Import core logic directly to avoid package issues
import reading.text_utils as text_utils
from reading.generator import ReadingGenerator

# Setup Mock DB and Config
db = MagicMock()
db.getAltFayin.side_effect = lambda word: [["ni3 hao3"]] if word == "你好" else False
db.get_simplified.side_effect = lambda x: x
db.get_traditional.side_effect = lambda x: x

config = MagicMock()
config.reading_type = "pinyin"

generator = ReadingGenerator(db, config)

def test_idempotency(input_text):
    print(f"\nTesting input: '{input_text}'")
    
    # Round 1
    cleaned1 = text_utils.strip_brackets(input_text)
    generated1 = generator.generate(cleaned1)
    print(f"Round 1: '{input_text}' -> '{cleaned1}' -> '{generated1}'")
    
    # Round 2
    cleaned2 = text_utils.strip_brackets(generated1)
    generated2 = generator.generate(cleaned2)
    print(f"Round 2: '{generated1}' -> '{cleaned2}' -> '{generated2}'")
    
    # Round 3
    cleaned3 = text_utils.strip_brackets(generated2)
    generated3 = generator.generate(cleaned3)
    print(f"Round 3: '{generated2}' -> '{cleaned3}' -> '{generated3}'")
    
    if generated1 == generated2 == generated3:
        print("RESULT: STABLE")
    else:
        print("RESULT: UNSTABLE (Potential Duplication)")

# Test cases
test_idempotency("你好")
test_idempotency("你好[ni3 hao3]")
test_idempotency("你好 [ni3 hao3]")
test_idempotency("你好&nbsp;[ni3 hao3]")
test_idempotency("<b>你好</b>[ni3 hao3]")
test_idempotency("你好[ni3 hao3][ni3 hao3]")
