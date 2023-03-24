from abc import ABC, abstractmethod
import mpmath
from database import create_connection, db_get_current_index, db_raise_current_index


# Contains all the Classes for Irrational numbers

# For rounding reasons, mpmath.mp.dps must be set 1 higher and the resulting string
# must be cut by the last digit in most functions.


class IrrationalDigits(ABC):
    name = ""
    first_digit = ""

    @staticmethod
    @abstractmethod
    def get_number_with_accuracy(accuracy):
        pass

    def get_digit_at_index(self, index):
        i_num = self.get_number_with_accuracy(index)
        return i_num[-1]

    def get_digits(self, index: int, amount: int) -> str:
        if index < 0 or amount < 0:
            print(f"index or amount too small in get_digits():\nindex={index} & amount={amount}")
            raise ValueError
        i_num = self.get_number_with_accuracy(index + amount)
        if index == 0:
            return i_num[-amount-2:]
        return i_num[-amount:]

    def get_next_digits_for_txt_file(self, amount: int, txt_path: str) -> str:
        with open(txt_path, "a+") as f:
            f.seek(0)
            current_number_of_digits = len(f.readline()) - 2
            if current_number_of_digits < 0:
                current_number_of_digits = 0
            next_digits = self.get_digits(current_number_of_digits, amount)
            f.write(next_digits)
            return next_digits

    def get_digits_for_user(self, user: str, amount: int, db_path: str) -> str:
        conn = create_connection(db_path)
        current_index = db_get_current_index(conn, user, self.name)
        if current_index < 0:
            return "error: user not found"
        last_ten = self.get_digits(current_index, amount)
        db_raise_current_index(conn, user, self.name, amount)
        return last_ten

    @staticmethod
    def get_all_from_file(txt_path):
        with open(txt_path, "a+") as f:
            f.seek(0)
            line = f.readline()
            if len(line) == 0:
                return ""
            return line


class MpMathNumbers(IrrationalDigits):
    @staticmethod
    @abstractmethod
    def get_mp_math_number():
        pass

    def get_number_with_accuracy(self, accuracy) -> str:
        if int(accuracy) == 0:  # Special case for first digit before "."
            return self.first_digit
        mpmath.mp.dps = accuracy + 2  # +2 for rounding
        i_num = str(self.get_mp_math_number())
        i_num = i_num.ljust(accuracy + 3, "0")
        return str(i_num)[:-1]


class Pi(MpMathNumbers):
    name = "pi"
    first_digit = "3"

    @staticmethod
    def get_mp_math_number():
        return mpmath.mp.pi


class E(MpMathNumbers):
    name = "e"
    first_digit = "2"

    @staticmethod
    def get_mp_math_number():
        return mpmath.mp.e


class Sqrt2(MpMathNumbers):
    name = "sqrt2"
    first_digit = "1"

    @staticmethod
    def get_mp_math_number():
        return mpmath.mp.sqrt(2)
