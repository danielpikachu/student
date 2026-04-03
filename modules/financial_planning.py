import streamlit as st

def render_financial_planning():
    """STUCO Constitution Module"""
    st.subheader("📜 STUCO Constitution")
    st.markdown("---")

    # ===================== Article I: Authority & Purpose =====================
    st.markdown("## 📌 Article I: Authority & Purpose")
    st.markdown("### Section 1: Mission Statement")
    st.write(
        "The mission of the SCIS High School Student Council (STUCO) is to represent the student body, advocate for student needs, "
        "and act as a catalyst for positive change within our school. We achieve this by developing student leaders, orchestrating events, "
        "and collaborating with faculty and administration teams to uphold the excellence of SCIS."
    )

    st.markdown("### Section 2: Vision")
    st.write(
        "To serve as the authentic, representative voice of the student body and to build a more inclusive, connected, and spirited school community."
    )

    st.markdown("### Section 3: Core Values")
    st.write("All actions taken by the Council must align with the five pillars:")
    st.write("• Community: Prioritizing inclusivity, collaboration, and service.")
    st.write("• Integrity: Acting honestly, ethically, and with strict accountability.")
    st.write("• Respect: Valuing different perspectives and treating others with dignity.")
    st.write("• Leadership: Inspiring peers through proactive initiative and responsibility.")
    st.write("• Growth: Committing to continuous personal development.")

    st.markdown("### Section 4: The Capstone Mandate")
    st.write(
        "The ultimate and final objective of STUCO each academic year is the successful execution of the High School Prom for the Grades 9–12 student body. "
        "Full participation is mandatory. Every STUCO member is explicitly required to contribute, plan, and assist in the operation of this capstone event."
    )
    st.markdown("---")

    # ===================== Article II: Leadership Structure =====================
    st.markdown("## 🧑‍🏫 Article II: Leadership Structure")
    st.markdown("### Section 1: The Executive Board")
    st.write(
        "The Executive Board consists of student leaders from the Grade 11 cohort (selected at the end of each academic year)."
    )

    st.markdown("### Section 2: Advisory Partnership")
    st.write(
        "Leaders operate in direct partnership with Faculty Advisors, the HS Principal, the Activities Coordinator, "
        "and the Operations Team to ensure all initiatives meet school standards."
    )
    st.markdown("---")

    # ===================== Article III: Membership & Admissions =====================
    st.markdown("## 📝 Article III: Membership & Admissions")
    st.markdown("### Section 1: Eligibility")
    st.write("Any student in Grades 9–11 at SCIS HQ is eligible to apply for Student Council.")

    st.markdown("### Section 2: The Application Process")
    st.write("1. Declaration of Interest: Applicants must complete the official STUCO Interest Form.")
    st.write("2. Resume Submission: Applicants must submit a one-page resume outlining academic achievements, extracurriculars, unique skills, and personal interests.")

    st.markdown("### Section 3: Acceptance Criteria & Weighting")
    st.write("Applications are reviewed objectively by current Leaders and Faculty Advisors based on:")
    st.write("• Leadership Experience (30%): Evaluation of previous roles (minor or major).")
    st.write("• Academic Performance (20%): Average to above-average academic standing.")
    st.write("• Community Engagement (25%): Demonstrated involvement in two or more activities.")
    st.write("• Commitment (25%): Willingness to display dedication to STUCO's mission.")
    st.markdown("---")

    # ===================== Article IV: Sub-Committees & Roles =====================
    st.markdown("## 🧩 Article IV: Sub-Committees & Roles")
    st.markdown("### Section 1: Functional Divisions")
    st.write(
        "To maintain operational efficiency, the Council is divided into subcommittees (focus groups). "
        "Every member must actively participate in at least one division (e.g., Social Media, Marketing, Event Planning, Logistics)."
    )
    st.markdown("---")

    # ===================== Article V: The Electoral Code =====================
    st.markdown("## 🗳️ Article V: The Electoral Code")
    st.markdown("### Section 1: Candidacy")
    st.write(
        "At the end of every academic year, students entering Grade 11 may run for a STUCO Executive Leader position."
    )

    st.markdown("### Section 2: The Election Process")
    st.write("1. The Address: Candidates must deliver a formal speech to the General Assembly outlining their platform.")
    st.write("2. Voting Weights: To ensure institutional stability, voting is weighted:")
    st.write("a. General Member Vote: 1 point")
    st.write("b. Faculty Advisor, Current Leader, & Admin Vote: 2 points")
    st.write("c. Formula:")
    # LaTeX公式渲染
    st.latex(r"S = \sum V_m + 2\sum V_f")
    st.markdown("---")

    # ===================== Article VI: The STUCO Credit & Reward System =====================
    st.markdown("## 🏆 Article VI: The STUCO Credit & Reward System")
    st.write(
        "To ensure fairness, transparency, and accountability, STUCO operates on a rigorous Credit System managed via the official STUCO website."
    )

    st.markdown("### Section 1: The Credit Ledger & The Digital Mandate")
    st.write(
        "The official ledger of all accumulated credits, penalties, and member standings is maintained dynamically on the STUCO management website. "
        "Members are required to constantly check the official website to stay updated on their credit status, attendance records, "
        "and dates for upcoming mandatory events. Ignorance of the website's contents is not a valid excuse for missed obligations."
    )

    st.markdown("### Section 2: The Credit Manager")
    st.write("A designated Credit Manager is responsible for:")
    st.write("• Monitoring attendance, volunteering, and specific event roles.")
    st.write("• Publishing monthly credit updates to STUCO Leaders and Faculty Advisors.")
    st.write("• Earning a baseline bonus of +10 credits per semester for their administrative labor.")

    st.markdown("### Section 3: Earning Credits")
    st.write("Credits are awarded based on participation and impact:")
    st.write("• Meeting Attendance: +2 credits (Present on time). Note: Excused absences yield 0 credits. While tardiness (arrival after 1:15 PM) is recorded, negative point deductions for lates are not currently implemented.")
    st.write("• Weekly Bubble Tea Sales: +1 credit per shift (Maximum 36 credits/year).")
    st.write("• Monthly Market Day: +3 credits per event (Maximum 27 credits/year).")
    st.write("• Event Leadership:")
    st.write("  o Sub-team Head/MC (Partial Event Lead): +6 credits.")
    st.write("  o End-to-End Organizer (Full Event Lead): +10 credits.")
    st.write("• Subcommittee Dedication (Per Semester):")
    st.write("  o Active Member: +5 credits.")
    st.write("  o Group Leader: +10 credits.")
    st.write("• Variable/Extraordinary Credits: Certain events may yield varying credits depending on importance. Exceptional dedication or extraordinary acts of service may be awarded up to +15 credits at the discretion of the Executive Board.")

    st.markdown("### Section 4: The Statute of Limitations on Credit Disputes")
    st.write(
        "If a member believes an error has been made regarding their attendance or credit allocation, "
        "they have exactly one (1) week from the time the update is posted on the website to file a dispute with the Leaders. "
        "No disputes, arguments, or corrections will be accepted after the one-week deadline."
    )

    st.markdown("### Section 5: The Rewards Tier")
    st.write("Accumulated credits can be redeemed for the following incentives:")
    st.write("• Tier 1 (Small): Bag of chips (40 credits) | Small café coupon/¥10 (50 credits).")
    st.write("• Tier 2 (Medium): Free bubble tea voucher (75 credits).")
    st.write("• Tier 3 (Premium): Free Prom Ticket (160 credits).")
    st.markdown("---")

    # ===================== Article VII: Meeting Protocols & General Guidelines =====================
    st.markdown("## 📅 Article VII: Meeting Protocols & General Guidelines")
    st.markdown("### Section 1: Logistics")
    st.write("• Schedule: Meetings convene every Monday at 1:15 PM in Mr. Iacobucci’s room (C01).")
    st.write("• Punctuality: Arrival after 1:20 PM officially constitutes a Late Mark.")
    st.write("• Cancellations: Sessions may be suspended due to Leader summative exams, Hyper Blocks, Faculty unavailability, or conflicting school events.")

    st.markdown("### Section 2: Floor Rules & Decorum")
    st.write("1. Digital Silence: Phones are strictly prohibited while STUCO is in session.")
    st.write("2. Culture of Respect: There are no bad ideas. Diminishing or disrespecting peers is entirely intolerable.")
    st.write("3. Originality: All ideas, proposals, and marketing materials must be original. Output completely generated by ChatGPT or other AI is not permitted.")

    st.markdown("### Section 3: Academic Priority & Teacher Communication Mandate")
    st.write(
        "While STUCO duties are important, academic responsibilities remain paramount."
    )
    st.write("• Members may not volunteer to skip a portion of class for STUCO duties more than once per month.")
    st.write("• The Burden of Communication: If a member is participating in a STUCO event during instructional time, it is strictly the member's responsibility to email their subject teachers in advance to secure permission and arrange make-up work.")
    st.write("• No Executive Bailouts: STUCO Leaders will absolutely not intervene, negotiate, or communicate with teachers on behalf of a member who failed to secure their own absence. Failure to notify teachers independently will result in immediate disciplinary action (See Article IX, Section 3).")
    st.markdown("---")

    # ===================== Article VIII: Event Operations & Proposals =====================
    st.markdown("## 🎉 Article VIII: Event Operations & Proposals")
    st.markdown("### Section 1: Independent Event Initiatives")
    st.write(
        "STUCO encourages innovation. If a member or sub-committee wishes to host an independent event outside of the standard calendar, "
        "they must strictly adhere to the following Chain of Approval:"
    )
    st.write("1. Executive Review: The proposal must first be pitched to and approved by the STUCO Leaders.")
    st.write("2. Faculty Review: If the Leaders approve, the proposal is escalated to the STUCO Faculty Advisors for vetting.")
    st.write("3. Administrative Authorization: Upon Faculty approval, the organizers must fill out the official event request form to secure final authorization from Ms. Corvers and Dr. Valerio. No planning may proceed without this final signature.")
    st.markdown("---")

    # ===================== Article IX: The Penal Code & Probation =====================
    st.markdown("## ⚖️ Article IX: The Penal Code & Probation")
    st.markdown("### Section 1: Academic & Credit-Based Removal")
    st.write("• The Minimum Standard: Members must earn a minimum of 25 credits per semester.")
    st.write("• Credit Probation: Accumulating only 20–24 credits results in a formal Probation Warning.")
    st.write("• Removal: Falling below 20 credits results in immediate removal from the Council.")
    st.write("• Election Eligibility: To run for leadership, a member must maintain ≥ 80% attendance credits and accrue ≥ 60 total credits by the end of the year.")

    st.markdown("### Section 2: Unexcused Absences")
    st.write("Members are allotted three unexcused absences per academic year:")
    st.write("• First Offense: Direct reminder from STUCO Leaders. (Penalty: -20 credits).")
    st.write("• Second Offense: Formal email from STUCO Leaders, cc’ing Faculty Advisors. (Penalty: -20 credits).")
    st.write("• Third Offense: Immediate removal from the Council.")

    st.markdown("### Section 3: Serious Offenses & Suspension")
    st.write(
        "Behaviors that damage the reputation of STUCO, violate SCIS policy, or breach trust will trigger immediate disciplinary action. Serious offenses include:"
    )
    st.write("• Failure to Notify Teachers: Missing class for a STUCO event without prior independent email communication with the subject teacher will result in the member being banned from participating in further STUCO events.")
    st.write("• Gross disrespect or insubordination toward peers, faculty, or administration.")
    st.write("• Using STUCO as a fraudulent justification for missing academic assignments.")
    st.write("• Financial mismanagement or theft of STUCO funds/inventory.")
    st.write("• Breaching STUCO confidentiality (e.g., leaking event themes, prom locations, or secure information before official release).")

    st.markdown("### Section 4: The Disciplinary Sanction")
    st.write("If a member commits a serious offense under Section 3:")
    st.write("1. They will be immediately stripped of any current leadership or sub-committee head titles.")
    st.write("2. They will be placed on strict Probationary Suspension, banning them from participating in any STUCO activities, events, or meetings for a minimum of one month.")
    st.write("3. This suspension may be extended indefinitely, or converted to permanent expulsion, pending a behavioral review by Faculty Advisors.")
    st.markdown("---")

    st.success("✅ STUCO Constitution - Version 3.0")
