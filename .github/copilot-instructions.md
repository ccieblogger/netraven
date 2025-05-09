---
applyTo: "**"
---

## Always start each chat conversation with "🤖 Hi! I'm Copilot, your IA assistant!"

### **Project Coding Principles**

#### **1. Code Quality and Maintainability**
- **Prefer Simple Solutions:** Always opt for straightforward and uncomplicated approaches to problem-solving. Simple code is easier to understand, test, and maintain.  
- **Avoid Code Duplication:** Strive to eliminate redundant code by checking for existing functionality before introducing new implementations. This aligns with the **DRY (Don't Repeat Yourself)** principle, which emphasizes reducing repetition to enhance maintainability.  
- **Refactor Large Files:** Keep individual files concise, ideally under **200-300 lines** of code. When files exceed this length, consider refactoring to improve readability and manageability.  

#### **2. Change Management**
- **Scope of Changes:** Only implement changes that are explicitly requested or directly related to the task at hand. Unnecessary modifications can introduce errors and complicate code reviews.  
- **Introduce New Patterns Cautiously:** When addressing bugs or issues, exhaust all options within the existing implementation before introducing new patterns or technologies. If a new approach is necessary, ensure that the old implementation is removed to prevent duplicate logic and legacy code.  
- **Deployment Considerations:** Always take into account the project's deployment model when introducing changes to ensure seamless integration and functionality in the deployment environment.  
- **Code Refactoring:** Code refactoring, enhancements, or significant changes should be done in a **Git feature branch** and reintroduced into the codebase through an **integration branch** after successful testing.  

#### **3. Resource Management**
- **Clean Up Temporary Resources:** Remove temporary files or code when they are no longer needed to maintain a clean and efficient codebase.  
- **Avoid Temporary Scripts in Files:** Refrain from writing scripts directly into files, especially if they are intended for one-time or temporary use. This practice helps maintain code clarity and organization.  

#### **4. Testing Practices**
- **Use Mock Data Appropriately:** Employ mock data exclusively for testing purposes. Avoid using mock or fake data in development or production environments to ensure data integrity and reliability.  

#### **5. Communication and Collaboration**
- **Propose and Await Approval for Plans:** When tasked with updates, enhancements, creation, or issue resolution, present a **detailed plan** outlining the proposed changes.  
   - Break the plan into phases to manage complexity and await approval before proceeding.  
   - Provide an updated plan with clear indications of progress after each successful set of changes.  
- **Seek Permission Before Advancing Phases:** Before moving on to the next phase, always obtain approval to ensure alignment with project goals and stakeholder expectations.  
- **Version Control Practices:** After successfully completing each phase:  
   - Perform a **Git state check**  
   - Commit the changes  
   - Ensuring a reliable version history and facilitating collaboration.  
- **Document Processes Clearly:** Without being overly verbose, provide **clear explanations** of your actions during coding, testing, or implementing changes. This transparency aids understanding and knowledge sharing among team members.  
- **Development Logging:** Maintain a log of changes, insights, and relevant information another developer could use to continue the current task.  
   - **GitHub Issues:** Update issue comments with development logging. Update frequently whenever significant changes or insights are found.  
   - **Non-GitHub Work:** Store logs in `/docs/developer_logs/` within a subfolder named after the feature branch.  
   - **Agent Mode:** When in agent mode, act as the developer—execute all code changes and commands except where specific commands are better suited to the user, in which case request their input.  