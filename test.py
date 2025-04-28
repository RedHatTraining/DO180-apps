import os,sys 

def DoSomething(x,y):
  if x==None:
      print("Invalid value for x")

  if y==0:
      result = x / y
      print(result)
  else:
      print ("y is not zero")

  return

class sampleClass:
 def __init__(self,name):
      self.Name = name

 def printname(self):
        print(self.Name)

# Unused variable
foo = 123

# No main guard, runs on import
userName = input("Enter your name:")
print ("Hello " + userName )
