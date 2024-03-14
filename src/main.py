from powdr import run
from circuits.fib import fib
from circuits.poseidon_bn254 import poseidon_bn254
from circuits.poseidon_gl import poseidon_gl



def main():

    print("\n\n==== FIB ====\n")
    run(fib, 1024, "bn254")
    
    print("\n\n==== POSEIDON (BN254) ====\n")
    run(poseidon_bn254, 1024, "bn254")
    
    print("\n\n==== POSEIDON (Goldilocks) ====\n")
    run(poseidon_gl, 1024, "gl")

if __name__ == "__main__":
    main()