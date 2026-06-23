import winsound
import sys

def main():
    frequency = 1000  # 1000 Hz
    duration = 500    # 500 ms
    
    # Optional arguments: frequency, duration
    if len(sys.argv) > 1:
        try:
            frequency = int(sys.argv[1])
        except ValueError:
            pass
    if len(sys.argv) > 2:
        try:
            duration = int(sys.argv[2])
        except ValueError:
            pass
            
    print(f"Playing system beep: {frequency}Hz for {duration}ms")
    winsound.Beep(frequency, duration)

if __name__ == "__main__":
    main()
