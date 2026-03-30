import Foundation

// MARK: - Diode Classes

class Diode {
	private var locked = false
	private let lockQueue = DispatchQueue(label: "diodeLock")
	private let resetTime: TimeInterval

	init(resetTime: TimeInterval = 2.0) {
		self.resetTime = resetTime
	}

	func forward(_ value: String) -> String? {
		var result: String?
		lockQueue.sync {
			if !locked {
				locked = true
				result = value
				DispatchQueue.global().asyncAfter(deadline: .now() + resetTime) {
					self.reset()
				}
			}
		}
		return result
	}

	func reset() {
		lockQueue.sync { self.locked = false }
	}

	func status() -> String { locked ? "Locked" : "Idle" }
}

class BidirectionalDiode {
	private var aQueue = [String]()
	private var bQueue = [String]()
	private let queueLock = DispatchQueue(label: "bidirectionalLock")

	func transferAtoB(_ value: String) {
		queueLock.sync { bQueue.append(value) }
	}

	func transferBtoA(_ value: String) {
		queueLock.sync { aQueue.append(value) }
	}

	func receiveA() -> String {
		queueLock.sync {
			if !aQueue.isEmpty { return aQueue.removeFirst() }
			return "-"
		}
	}

	func receiveB() -> String {
		queueLock.sync {
			if !bQueue.isEmpty { return bQueue.removeFirst() }
			return "-"
		}
	}
}

// MARK: - Oscillator

class Oscillator {
	private let frequencyHz: Double
	private let callback: (String) -> Void
	private var timer: Timer?

	init(frequencyHz: Double, callback: @escaping (String) -> Void) {
		self.frequencyHz = frequencyHz
		self.callback = callback
	}

	func start() {
		timer = Timer.scheduledTimer(withTimeInterval: 1.0 / frequencyHz, repeats: true) { _ in
			self.callback("tick")
		}
		RunLoop.current.add(timer!, forMode: .common)
	}

	func stop() {
		timer?.invalidate()
		timer = nil
	}
}

// MARK: - Network Setup

let entryDiode = Diode()
let bidirectional = BidirectionalDiode()
var score = 0
var log = [String]()

func oscillatorOutput(value: String) {
	bidirectional.transferAtoB(value)
	bidirectional.transferBtoA(value)
	log.append("Oscillator tick")
}

let osc = Oscillator(frequencyHz: 1, callback: oscillatorOutput)
osc.start()

// MARK: - Jail Shell Functions

func printStatus() {
	print("\n=== Status ===")
	print("Entry Diode: \(entryDiode.status())")
	print("A-side: \(bidirectional.receiveA())")
	print("B-side: \(bidirectional.receiveB())")
	print("Score: \(score)")
	print("Recent Log:")
	for msg in log.suffix(5) {
		print("  \(msg)")
	}
	print("================\n")
}

func processCommand(_ cmd: String) -> Bool {
	let command = cmd.trimmingCharacters(in: .whitespacesAndNewlines)

	if command.lowercased() == "exit" {
		// Block exit completely
		log.append("Exit blocked by diode")
		print("\n[Blocked] Cannot exit the jail!\n")
		score = max(0, score - 1)
		printStatus()
		return true
	} else if command.lowercased() == "reset" {
		entryDiode.reset()
		log.append("Entry diode reset")
		printStatus()
		return true
	} else if command.isEmpty {
		return true
	}

	// Attempt to pass through the entry diode
	if entryDiode.forward(command) != nil {
		log.append("Entry diode passed command: \(command)")
		print("\n[Entry diode passed] Executing: \(command)\n")

		let process = Process()
		process.launchPath = "/bin/zsh" // Zsh shell
		process.arguments = ["-c", command]

		let pipe = Pipe()
		process.standardOutput = pipe
		process.standardError = pipe

		process.launch()
		process.waitUntilExit()

		// Read all output (with colors)
		let data = pipe.fileHandleForReading.readDataToEndOfFile()
		if let output = String(data: data, encoding: .utf8) {
			print(output, terminator: "") // ANSI color codes preserved
		}

		score += 1
	} else {
		log.append("Entry diode blocked command: \(command)")
		print("\n[Blocked by diode] Cannot execute: \(command)\n")
		score = max(0, score - 1)
	}

	printStatus()
	return true
}

// MARK: - Main Shell Loop

print("=== Swift Diode Zsh Jail (Exit Disabled, Colors Allowed) ===")
print("All commands are trapped by a diode. Type 'reset' to reset entry diode.\n")

while true {
	print("zsh> ", terminator: "")
	guard let input = readLine() else {
		print("\nEOF received. Continuing...")
		continue // ignore EOF, keep jail running
	}
	_ = processCommand(input)
}