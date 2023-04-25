from time import time


def time_function(func):
    # This function shows the execution time of 
    # the function object passed
    def wrap_func(*args, **kwargs):
        t1 = time()
        result = func(*args, **kwargs)
        t2 = time()
        print(f'Function {func.__name__!r} executed in {(t2-t1):.4f}s')
        return result
    return wrap_func


def longest_common_substring(s1, s2):
    if len(s1) > len(s2):
        long_str, short_str = s1, s2
    else:
        long_str, short_str = s2, s1

    m = len(short_str)
    longest_substring = ""

    while m > 0:
        for i in range(len(short_str) - m + 1):
            substring = short_str[i:i + m]
            if substring in long_str:
                longest_substring = substring
                return longest_substring
        m -= 1

    return longest_substring

def float_to_dollar(amount):
    dollars = int(amount)
    cents = int(round((amount - dollars) * 10000))
    return "${}.{:04d}".format(dollars, cents)


