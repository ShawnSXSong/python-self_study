def square_sum(a,b):
    """return the square sum of two arguments
        sample: square(a,b)"""
    a,b = int(a),int(b) #insure data type suit to this function
    a,b = a**2,b**2
    c = a + b
    return c

a,b = input("first num:"),input("second num:")
c = square_sum(a,b)
print(c)
#help(square_sum)
