def electric_bill(n):
    if n>0 and n<=150:
        print(f"Electric Bill is {n*3}")
    if n>=151 and n<=350:
        remaining = n-150
        print(f"electric bill is {(n*3)+(103.75*remaining)}")
    if n>=351 and n<=450:
        remaining = n-150
        print(f"electric bill is {(n*3)+(254*remaining)}")
    if n>=450 and n<=600:
        remaining = n-150
        print(f"electric bill is {(n*3)+(304.25*remaining)}")
    if n>600:
        remaining = n-150
        print(f"electric bill is {(n*3)+(405*remaining)}")
    return


n = 200
electric_bill(n)