from isa import from_bytes_instruction

def main(code_file, input_file):
    with open(code_file, 'rb') as f:
        binary_instruction = f.read()

    print(binary_instruction)

    print(from_bytes_instruction(binary_instruction))

if __name__ == "__main__":
    main("instruction_memory.bin", ".")