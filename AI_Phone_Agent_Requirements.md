# AI Phone Agent - Requirements for PBX Provider

## Business: Hodler Inn (Hotel)
## Client: Railroad Crews (CPKC - Canadian Pacific Kansas City)

---

## Current Problem

Our hotel serves railroad crews who have **random check-in and check-out times**. When crew members need to go on duty, CPKC's automated system calls our hotel to wake them up.

**Current Manual Process:**
1. CPKC automated system calls hotel (any time, day or night)
2. System says: *"This is CPKC calling for [Employee Name or Employee Number]. When you are prepared to transfer, press 6"*
3. Front desk answers and presses **6**
4. Front desk looks up employee name/number to find their room number
5. Front desk transfers the call to the employee's room

**Problem:** This requires someone to be awake 24/7 to answer and transfer calls.

---

## Desired Solution: AI Phone Agent

We want to automate this process with an AI agent that:

1. **Automatically answers** incoming calls from CPKC
2. **Listens and understands** the employee name OR employee number
3. **Presses 6** (DTMF tone) when prompted
4. **Looks up the room number** from our hotel database
5. **Transfers the call** to the correct room

---

## Call Scenarios

### Scenario 1: Call by Employee Name
```
CPKC System: "This is CPKC calling for LOPEZ, RICHARD. When you are prepared to transfer, press 6"
AI Agent: [Presses 6]
AI Agent: [Looks up "LOPEZ, RICHARD" → Room 111]
AI Agent: [Transfers call to Room 111]
```

### Scenario 2: Call by Employee Number
```
CPKC System: "This is CPKC calling for 001185196. When you are prepared to transfer, press 6"
AI Agent: [Presses 6]
AI Agent: [Looks up Employee #1185196 → Room 212]
AI Agent: [Transfers call to Room 212]
```

---

## What We Need From PBX Provider

Please let us know if your system supports:

### 1. API Access
- [ ] REST API for call control?
- [ ] Webhook notifications for incoming calls?
- [ ] Programmable call handling?

### 2. Call Answering
- [ ] Can an external system (AI) answer calls automatically?
- [ ] Can we intercept calls before they ring front desk?

### 3. DTMF Tones
- [ ] Can we send DTMF tones (press 6) programmatically via API?

### 4. Call Transfer
- [ ] Can we transfer calls to room extensions via API?
- [ ] What is the format? (e.g., dial extension 111 for Room 111)

### 5. Speech/Audio
- [ ] Can we access the audio stream of incoming calls?
- [ ] Do you support integration with speech-to-text services?

### 6. Third-Party Integration
- [ ] Do you support Twilio integration?
- [ ] Do you have documentation for developers/API?

---

## Technical Integration Options

We are flexible and can work with:

**Option A:** Use your PBX's built-in IVR/automation features
**Option B:** Connect via your API to our AI system
**Option C:** Use Twilio as middleware between CPKC and your PBX

---

## Our System (Already Built)

We already have:
- Guest database with employee names, employee numbers, and room assignments
- Web portal for check-in/check-out management
- Name matching system that can find employees by name or number

We just need the phone/PBX integration to complete the automation.

---

## Questions for Provider

1. What is the best way to integrate an AI call handler with your system?
2. Do you have an API? If yes, please share documentation.
3. What are the costs for API access or advanced features?
4. Do you have experience with similar automations?
5. Can you recommend a solution that fits our needs?

---

## Contact

Please respond with:
- Available integration options
- API documentation (if available)
- Pricing for required features
- Recommended approach

Thank you!
