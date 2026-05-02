from isa import from_bytes_instruction, from_bytes_data

def main(code_file, mem_file, input_file):
    with open(code_file, 'rb') as f:
        binary_instruction = f.read()

    print(binary_instruction)

    with open(mem_file, 'rb') as f:
        binary_memory = f.read()

    print(binary_memory)
    print(from_bytes_data(binary_memory))
    print(from_bytes_instruction(binary_instruction))

if __name__ == "__main__":
    main("instruction_memory.bin", "data_memory.bin", ".")