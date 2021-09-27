
import threading, random, time
class ThreadTest:
    def __init__(self,count):
        self.count = count
        self.innerCount = 0
        self.startAll()

    def startAll(self):
        threads = list()
        for _ in range(self.count):
            t = threading.Thread(target=self.startOne)
            t.start()
            threads.append(t)
        for thread in threads:
            thread.join()

    def startOne(self):
        sleepTime = random.randint(0, 5)
        time.sleep(sleepTime)
        self.innerCount += 1

if __name__ == "__main__":
    test = ThreadTest(5000)
    print(test.innerCount)