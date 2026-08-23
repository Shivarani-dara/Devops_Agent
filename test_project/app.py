def add_numbers(a, b):
    if isinstance(b, str):  # Check if b is a string
        b = int(b)  # Convert b to integer
    return a + b
if __name__ == "__main__":
    add_numbers(9,100)

   
