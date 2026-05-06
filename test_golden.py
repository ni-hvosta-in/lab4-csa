import os
import tempfile

import pytest

import machine
import translator

@pytest.mark.golden_test("golden/*.yml")
def test_translator_and_machine(golden):
    with tempfile.TemporaryDirectory() as tmpdirname:

        test_name = os.path.basename(str(golden.path))

        source = os.path.join(tmpdirname, "source.s")
        input_stream = os.path.join(tmpdirname, "input.txt")

        code_file = os.path.join(tmpdirname, "code.bin")
        data_file = os.path.join(tmpdirname, "data.bin")

        with open(source, "w", encoding="utf-8") as file:
            file.write(golden["in_source"])

        with open(input_stream, "w", encoding="utf-8") as file:
            file.write(golden["in_stdin"])

        translator.main(source, code_file, data_file)

        debug = test_name != "prob1.yml"

        machine.main(code_file, data_file, input_stream, debug)

        with open(code_file, "rb") as file:
            code = file.read()

        with open(data_file, "rb") as file:
            data = file.read()

        with open("instruction_logs.txt", encoding="utf-8") as file:
            instruction_log = file.read()

        with open("variable_logs.txt", encoding="utf-8") as file:
            variable_log = file.read()

        with open("machine.log", encoding="utf-8") as file:
            machine_log = file.read()

        assert code == golden.out["out_code"]

        assert data == golden.out["out_data"]

        assert instruction_log == golden.out["out_instruction_log"]

        assert variable_log == golden.out["out_variable_log"]

        assert machine_log == golden.out["out_machine_log"]