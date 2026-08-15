def add_numbers(a, b):
  if b == 0:
    raise ValueError('Division by zero')
  else:
    return a/b
if __name__ == "__main__":
    x = add_numbers(10, "900")
    print(x)