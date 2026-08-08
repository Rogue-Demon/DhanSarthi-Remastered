धनSarthi --- Frontend UI (React)

Overview

धनSarthi is a modern AI-powered financial management dashboard built
with React. The goal of this project is to create a premium, responsive,
scalable, and user-friendly frontend that provides personalized
financial management experiences for different user profiles.

This phase focuses only on the frontend. No backend, authentication,
APIs, databases, or AI integrations should be implemented. Use mock data
wherever necessary.

------------------------------------------------------------------------

📌 Development Instructions

Important

This project includes a separate document named PROJECT_GUIDELINES.md.

Before implementing any page, layout, or component, read and follow
PROJECT_GUIDELINES.md.

Priority Order

1.  UI Guidelines (provided separately) Highest Priority
2.  PROJECT_GUIDELINES.md
3.  README.md
4.  React & JavaScript Best Practices

If any conflict occurs, always follow the UI Guidelines.

------------------------------------------------------------------------

🎯 Project Goal

Build a modern fintech dashboard that allows users to:

-   View personalized dashboards
-   Manage finances visually
-   Track investments
-   View reports
-   Interact with an AI Financial Advisor (Frontend UI Only)

The application should feel polished, premium, and similar to a modern
banking or investment platform.

------------------------------------------------------------------------

User Profiles

The application supports three user profiles.

Student

Focus Areas

-   Allowance
-   Scholarships
-   Savings
-   Education Expenses
-   Budget Planning
-   Savings Goals

------------------------------------------------------------------------

Working Professional

Focus Areas

-   Salary
-   Side Income
-   Monthly Expenses
-   Savings
-   Assets
-   Liabilities
-   Budget
-   Tax Overview
-   Investment Summary

------------------------------------------------------------------------

Business

Focus Areas

-   Revenue
-   Profit
-   Expenses
-   Cash Flow
-   Payroll
-   Inventory
-   Outstanding Payments
-   Budget

------------------------------------------------------------------------

Sidebar

The sidebar must be personalized according to the selected profile.

Each profile should display only the relevant navigation options.

Student Sidebar

-   Dashboard
-   Profile
-   Finance
-   Investments
-   AI Advisor
-   Reports
-   Settings

------------------------------------------------------------------------

Working Professional Sidebar

-   Dashboard
-   Profile
-   Finance
-   Investments
-   AI Advisor
-   Reports
-   Settings

------------------------------------------------------------------------

Business Sidebar

-   Dashboard
-   Profile
-   Finance
-   Investments
-   AI Advisor
-   Reports
-   Settings

Although the navigation labels remain the same, the content inside every
page must change according to the selected user profile.

------------------------------------------------------------------------

Finance Module

Finance includes

-   Overview
-   Income
-   Expenses
-   Assets
-   Liabilities
-   Budget
-   Cash Flow
-   Goals

The displayed information must be customized for each profile.

------------------------------------------------------------------------

Investments Module

Provide UI for

-   Portfolio
-   Stocks
-   Mutual Funds
-   SIP
-   Fixed Deposit (FD)
-   Recurring Deposit (RD)
-   Gold
-   Bonds
-   PPF
-   NPS

This module is UI only.

------------------------------------------------------------------------

AI Advisor

The application contains only one Smart Tool.

AI Financial Advisor

The page should include

-   Chat Interface
-   Conversation History
-   Suggested Prompts
-   Chat Input
-   Modern Messaging Layout

Example Questions

-   Can I afford this purchase?
-   Help me create a monthly budget.
-   Suggest an investment strategy.
-   Where am I overspending?
-   How can I save more money?
-   Help me reach my savings goal.

------------------------------------------------------------------------

Reports

Create UI for

-   Daily Report
-   Weekly Report
-   Monthly Report
-   Annual Report

Include

-   Charts
-   Tables
-   Summary Cards
-   Export Button (UI Only)

------------------------------------------------------------------------

Dashboard

Student Dashboard

Cards

-   Monthly Allowance
-   Savings
-   Monthly Expenses
-   Education Expenses
-   Budget Remaining
-   Goal Progress

------------------------------------------------------------------------

Working Professional Dashboard

Cards

-   Salary
-   Expenses
-   Savings
-   Assets
-   Liabilities
-   Investment Summary
-   Net Worth
-   Tax Overview

------------------------------------------------------------------------

Business Dashboard

Cards

-   Revenue
-   Expenses
-   Profit
-   Cash Flow
-   Payroll
-   Inventory
-   Outstanding Payments
-   Budget

------------------------------------------------------------------------

Charts

Use charts for

-   Income vs Expenses
-   Expense Categories
-   Investment Allocation
-   Cash Flow
-   Net Worth Growth
-   Goal Progress

------------------------------------------------------------------------

Design

Theme

Modern FinTech Dashboard

Design Principles

-   Clean
-   Minimal
-   Premium
-   Responsive
-   Consistent

Suggested Colors

-   Primary Blue
-   Secondary Emerald
-   Accent Purple
-   Background White / Light Gray

------------------------------------------------------------------------

Tech Stack

-   React
-   JavaScript (JSX)
-   Vite
-   Tailwind CSS
-   React Router
-   Zustand
-   React Query
-   Recharts
-   Framer Motion
-   shadcn/ui

------------------------------------------------------------------------

📁 Suggested Structure

src/

-   assets/
-   components/
-   constants/
-   hooks/
-   layouts/
-   pages/
-   routes/
-   store/
-   types/
-   utils/

  ------------
  Responsive
  Design

  Support

  \- Desktop -
  Laptop -
  Tablet -
  Mobile
  ------------

🚀 Future Ready

Keep the architecture modular so future backend services, APIs, AI
integrations, authentication, and databases can be integrated without
major frontend changes.

------------------------------------------------------------------------

📌 Final Objective

## Build a production-quality, AI-first fintech frontend with personalized dashboards, reusable React components, modern UI/UX, and a scalable architecture while strictly following the provided UI Guidelines.

PROJECT_GUIDELINES.md

धनSarthi--- Project Development Guidelines

Purpose

This document defines the engineering and development standards for the
project.

Every page, component, and feature must follow these guidelines.

------------------------------------------------------------------------

1.  Highest Priority

Always follow the documents in this order.

1.  UI Guidelines (Highest Priority)
2.  PROJECT_GUIDELINES.md
3.  README.md

If there is any conflict, always follow the UI Guidelines.

------------------------------------------------------------------------

2.  Project Scope

-   AI Integration
-   Business Logic
-   Payment Gateway
-   Real Data Storage

Use mock data wherever necessary.

------------------------------------------------------------------------

3.  Development Philosophy

Build the application as if it will later become a production-ready
fintech platform.

Prioritize

-   Scalability
-   Reusability
-   Maintainability
-   Readability
-   Performance

------------------------------------------------------------------------

4.  Folder Structure

Use a clean modular structure.

Example

src/

components/

pages/

layouts/

hooks/

store/

constants/

types/

utils/

assets/

routes/

------------------------------------------------------------------------

5.  Components

Create reusable components.

Examples

-   Sidebar
-   Navbar
-   Dashboard Card
-   Statistic Card
-   Chart Card
-   Table
-   Button
-   Input
-   Modal
-   AI Chat Message
-   Profile Card

Avoid duplicate UI code.

------------------------------------------------------------------------

6.  Dashboard

Never create three different dashboard projects.

Use one dashboard layout that loads widgets dynamically based on the
selected user profile.

Student

↓

Student Widgets

Professional

↓

Professional Widgets

Business

↓

Business Widgets

------------------------------------------------------------------------

7.  Sidebar

The sidebar should be personalized according to the selected user
profile.

Only show the navigation options relevant to that profile.

Keep the navigation clean and uncluttered.

------------------------------------------------------------------------

8.  Routing

Suggested routes

/

dashboard

profile

finance

investments

ai-advisor

reports

settings

------------------------------------------------------------------------

9.  Code Standards

Use

-   JavaScript (JSX)
-   Functional Components
-   React Hooks
-   Modern JavaScript Best Practices
-   Clean Imports

Avoid

-   Duplicate Logic
-   Large Components
-   Hardcoded Values
-   Unnecessary Re-renders

------------------------------------------------------------------------

10. UI Consistency

Maintain consistency in

-   Typography
-   Colors
-   Icons
-   Shadows
-   Border Radius
-   Animations
-   Card Design
-   Buttons
-   Spacing

Never mix different design styles.

------------------------------------------------------------------------

11. Responsive Design

Support

-   Mobile
-   Tablet
-   Laptop
-   Desktop

Layouts must never break.

------------------------------------------------------------------------

12. Performance

-   Lazy load pages
-   Reuse components
-   Optimize rendering
-   Avoid unnecessary state updates

------------------------------------------------------------------------

13. State Management

Use global state only for

-   User Profile
-   Theme
-   Sidebar State

Keep component state local wherever possible.

------------------------------------------------------------------------

14. AI Advisor

The AI Advisor is a core feature.

For this frontend phase, create only the interface.

Include

-   Chat Window
-   Chat History
-   Suggested Questions
-   Message Input
-   Responsive Layout

No AI functionality is required.

------------------------------------------------------------------------

15. Charts

Use Recharts.

Charts should have

-   Tooltips
-   Legends
-   Responsive Containers
-   Consistent Styling

------------------------------------------------------------------------

16. Accessibility

Ensure

-   Semantic HTML
-   Keyboard Navigation
-   Proper Labels
-   Focus States
-   Accessible Color Contrast

------------------------------------------------------------------------

17. Error & Empty States

Provide proper UI for

-   Loading
-   Empty Data
-   Error Messages
-   Missing Information

------------------------------------------------------------------------

18. Reusability

Every section should be designed for future expansion.

Avoid hardcoding profile-specific layouts.

Instead, configure layouts through reusable components and data-driven
rendering.

------------------------------------------------------------------------

19. Coding Principles

Always follow

-   DRY (Don't Repeat Yourself)
-   SOLID Principles
-   Separation of Concerns
-   Modular Architecture
-   Component Reusability

------------------------------------------------------------------------
