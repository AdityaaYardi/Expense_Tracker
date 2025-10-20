import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os

# Page configuration
st.set_page_config(page_title="Personal Budget Tracker", page_icon="💰", layout="wide")

# File to store data
DATA_FILE = "budget_data.json"

def save_data():
    """Save data to JSON file"""
    with open(DATA_FILE, 'w') as f:
        json.dump(st.session_state.data, f, indent=2)

# Initialize session state
if 'data' not in st.session_state:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            st.session_state.data = json.load(f)
        # Migrate old data to new format
        if 'savings_account' not in st.session_state.data:
            st.session_state.data['savings_account'] = 0.0
        if 'savings_transactions' not in st.session_state.data:
            st.session_state.data['savings_transactions'] = []
        save_data()
    else:
        st.session_state.data = {
            'income': [],
            'expenses': [],
            'savings_account': 0.0,
            'savings_transactions': [],
            'settings': {
                'daily_budget': 20.0,
                'week_start': 'Monday'
            }
        }

def add_income(amount, description, date):
    """Add income entry to current account"""
    st.session_state.data['income'].append({
        'amount': amount,
        'description': description,
        'date': date.strftime('%Y-%m-%d'),
        'timestamp': datetime.now().isoformat(),
        'account': 'current'
    })
    save_data()

def add_expense(amount, description, category, date):
    """Add expense entry from current account"""
    st.session_state.data['expenses'].append({
        'amount': amount,
        'description': description,
        'category': category,
        'date': date.strftime('%Y-%m-%d'),
        'timestamp': datetime.now().isoformat(),
        'account': 'current'
    })
    save_data()

def add_to_savings(amount, description, date):
    """Add money to savings account"""
    st.session_state.data['savings_account'] += amount
    st.session_state.data['savings_transactions'].append({
        'amount': amount,
        'description': description,
        'date': date.strftime('%Y-%m-%d'),
        'timestamp': datetime.now().isoformat(),
        'type': 'deposit'
    })
    save_data()

def withdraw_from_savings(amount, description, date):
    """Withdraw money from savings account"""
    if st.session_state.data['savings_account'] >= amount:
        st.session_state.data['savings_account'] -= amount
        st.session_state.data['savings_transactions'].append({
            'amount': amount,
            'description': description,
            'date': date.strftime('%Y-%m-%d'),
            'timestamp': datetime.now().isoformat(),
            'type': 'withdrawal'
        })
        save_data()
        return True
    return False

def delete_income(index):
    """Delete income entry by index"""
    if 0 <= index < len(st.session_state.data['income']):
        del st.session_state.data['income'][index]
        save_data()

def delete_expense(index):
    """Delete expense entry by index"""
    if 0 <= index < len(st.session_state.data['expenses']):
        del st.session_state.data['expenses'][index]
        save_data()

def calculate_budget_status():
    """Calculate current budget status and allowances for current account"""
    daily_budget = st.session_state.data['settings']['daily_budget']
    
    # Get total income (current account)
    total_income = sum(item['amount'] for item in st.session_state.data['income'])
    
    # Get total expenses (current account)
    total_expenses = sum(item['amount'] for item in st.session_state.data['expenses'])
    
    # Calculate current account balance
    current_account_balance = total_income - total_expenses
    
    # Calculate expenses by week
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())
    
    # Current week expenses
    current_week_expenses = sum(
        item['amount'] for item in st.session_state.data['expenses']
        if datetime.strptime(item['date'], '%Y-%m-%d').date() >= week_start
    )
    
    # Calculate days in current week so far
    days_this_week = (today - week_start).days + 1
    
    # Expected spending for this week
    expected_spending = daily_budget * days_this_week
    
    # Rollover from not spending full daily budget
    rollover = expected_spending - current_week_expenses
    
    # Available today (daily budget + rollover)
    available_today = daily_budget + max(0, rollover)
    
    return {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'current_account_balance': current_account_balance,
        'savings_balance': st.session_state.data['savings_account'],
        'daily_budget': daily_budget,
        'current_week_expenses': current_week_expenses,
        'expected_spending': expected_spending,
        'rollover': rollover,
        'available_today': available_today,
        'days_this_week': days_this_week
    }

# App title
st.title("💰 Personal Budget Tracker")
st.markdown("Track your income and expenses with daily budget allowances")

# Savings Account Banner at the top
budget_status = calculate_budget_status()

st.markdown("---")
col1, col2, col3 = st.columns([2, 2, 2])

with col1:
    st.markdown("### 🏦 Savings Account")
    st.metric("Total Savings", f"€{budget_status['savings_balance']:.2f}", help="Your savings account balance")

with col2:
    st.markdown("### 💳 Current Account")
    st.metric("Available Balance", f"€{budget_status['current_account_balance']:.2f}", help="Income minus expenses")

with col3:
    st.markdown("### 💰 Total Wealth")
    total_wealth = budget_status['savings_balance'] + budget_status['current_account_balance']
    st.metric("Combined Total", f"€{total_wealth:.2f}", help="Savings + Current Account")

st.markdown("---")

# Sidebar for settings
with st.sidebar:
    st.header("⚙️ Settings")
    daily_budget = st.number_input(
        "Daily Budget Allowance (€)",
        min_value=0.0,
        value=st.session_state.data['settings']['daily_budget'],
        step=1.0,
        help="Your base daily spending allowance"
    )
    
    if daily_budget != st.session_state.data['settings']['daily_budget']:
        st.session_state.data['settings']['daily_budget'] = daily_budget
        save_data()
    
    st.divider()
    
    # Export/Import data
    st.subheader("📊 Data Management")
    if st.button("Export Data"):
        st.download_button(
            label="Download JSON",
            data=json.dumps(st.session_state.data, indent=2),
            file_name=f"budget_data_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )

# Main content tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Dashboard", "💵 Add Income", "💸 Add Expense", "🏦 Savings Account", "📈 History"])

with tab1:
    st.header("Budget Dashboard")
    
    budget_status = calculate_budget_status()
    
    # Key metrics for Current Account
    st.subheader("💳 Current Account Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Income", f"€{budget_status['total_income']:.2f}")
    
    with col2:
        st.metric("Total Expenses", f"€{budget_status['total_expenses']:.2f}")
    
    with col3:
        st.metric("Current Balance", f"€{budget_status['current_account_balance']:.2f}")
    
    with col4:
        st.metric("Daily Budget", f"€{budget_status['daily_budget']:.2f}")
    
    st.divider()
    
    # This week's summary
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📅 This Week Summary")
        st.metric(
            "Spent This Week",
            f"€{budget_status['current_week_expenses']:.2f}",
            f"-{budget_status['current_week_expenses']:.2f}"
        )
        st.metric(
            "Expected Spending",
            f"€{budget_status['expected_spending']:.2f}",
            help=f"Based on {budget_status['days_this_week']} days × €{budget_status['daily_budget']}/day"
        )
    
    with col2:
        st.subheader("💳 Available Today")
        rollover = budget_status['rollover']
        
        if rollover > 0:
            st.success(f"You have **€{budget_status['available_today']:.2f}** available today!")
            st.info(f"Includes €{rollover:.2f} rollover from unspent budget this week 🎉")
        elif rollover < 0:
            st.warning(f"You've overspent by €{abs(rollover):.2f} this week")
            st.metric("Available Today", f"€{budget_status['daily_budget']:.2f}")
        else:
            st.info(f"You have **€{budget_status['available_today']:.2f}** available today")
    
    # Progress bar for weekly budget
    if budget_status['expected_spending'] > 0:
        progress = min(budget_status['current_week_expenses'] / budget_status['expected_spending'], 1.0)
        st.progress(progress)
        st.caption(f"Week Progress: {progress*100:.1f}% of expected spending")

with tab2:
    st.header("💵 Add Income (Current Account)")
    
    with st.form("income_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            income_amount = st.number_input("Amount (€)", min_value=0.01, step=1.0)
            income_date = st.date_input("Date", value=datetime.now())
        
        with col2:
            income_description = st.text_input("Description", placeholder="e.g., Salary, Freelance work")
        
        submitted = st.form_submit_button("Add Income to Current Account", type="primary")
        
        if submitted:
            if income_description:
                add_income(income_amount, income_description, income_date)
                st.success(f"Added €{income_amount:.2f} to current account!")
                st.rerun()
            else:
                st.error("Please provide a description")

with tab3:
    st.header("💸 Add Expense (Current Account)")
    
    with st.form("expense_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            expense_amount = st.number_input("Amount (€)", min_value=0.01, step=1.0)
            expense_date = st.date_input("Date", value=datetime.now())
        
        with col2:
            expense_category = st.selectbox(
                "Category",
                ["Food", "Transport", "Entertainment", "Shopping", "Bills", "Healthcare", "Other"]
            )
            expense_description = st.text_input("Description", placeholder="e.g., Lunch, Gas")
        
        submitted = st.form_submit_button("Add Expense from Current Account", type="primary")
        
        if submitted:
            if expense_description:
                add_expense(expense_amount, expense_description, expense_category, expense_date)
                st.success(f"Added expense of €{expense_amount:.2f} from current account")
                st.rerun()
            else:
                st.error("Please provide a description")

with tab4:
    st.header("🏦 Savings Account Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💰 Deposit to Savings")
        with st.form("savings_deposit_form"):
            deposit_amount = st.number_input("Amount (€)", min_value=0.01, step=1.0, key="deposit")
            deposit_date = st.date_input("Date", value=datetime.now(), key="deposit_date")
            deposit_description = st.text_input("Description", placeholder="e.g., Monthly savings", key="deposit_desc")
            
            if st.form_submit_button("Deposit to Savings", type="primary"):
                if deposit_description:
                    add_to_savings(deposit_amount, deposit_description, deposit_date)
                    st.success(f"Added €{deposit_amount:.2f} to savings account!")
                    st.rerun()
                else:
                    st.error("Please provide a description")
    
    with col2:
        st.subheader("💸 Withdraw from Savings")
        with st.form("savings_withdrawal_form"):
            withdrawal_amount = st.number_input("Amount (€)", min_value=0.01, step=1.0, key="withdrawal")
            withdrawal_date = st.date_input("Date", value=datetime.now(), key="withdrawal_date")
            withdrawal_description = st.text_input("Description", placeholder="e.g., Emergency fund", key="withdrawal_desc")
            
            if st.form_submit_button("Withdraw from Savings", type="secondary"):
                if withdrawal_description:
                    if withdraw_from_savings(withdrawal_amount, withdrawal_description, withdrawal_date):
                        st.success(f"Withdrew €{withdrawal_amount:.2f} from savings account!")
                        st.rerun()
                    else:
                        st.error("Insufficient funds in savings account!")
                else:
                    st.error("Please provide a description")
    
    # Savings transaction history
    st.divider()
    st.subheader("📊 Savings Transaction History")
    
    if st.session_state.data.get('savings_transactions'):
        savings_df = pd.DataFrame(st.session_state.data['savings_transactions'])
        savings_df = savings_df.sort_values('date', ascending=False).reset_index(drop=True)
        
        for idx, row in savings_df.iterrows():
            col_a, col_b, col_c, col_d = st.columns([2, 2, 3, 2])
            with col_a:
                st.text(row['date'])
            with col_b:
                if row['type'] == 'deposit':
                    st.markdown(f"✅ **Deposit**")
                else:
                    st.markdown(f"❌ **Withdrawal**")
            with col_c:
                st.text(row['description'])
            with col_d:
                if row['type'] == 'deposit':
                    st.markdown(f"**+€{row['amount']:.2f}**")
                else:
                    st.markdown(f"**-€{row['amount']:.2f}**")
    else:
        st.info("No savings transactions yet")

with tab5:
    st.header("📈 Transaction History")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Recent Income")
        if st.session_state.data['income']:
            income_df = pd.DataFrame(st.session_state.data['income'])
            income_df = income_df.sort_values('date', ascending=False).reset_index(drop=True)
            
            # Display with delete buttons
            for idx, row in income_df.iterrows():
                # Find original index in unsorted data
                original_idx = len(st.session_state.data['income']) - 1 - idx
                
                col_a, col_b, col_c, col_d = st.columns([2, 3, 2, 1])
                with col_a:
                    st.text(row['date'])
                with col_b:
                    st.text(row['description'])
                with col_c:
                    st.text(f"€{row['amount']:.2f}")
                with col_d:
                    if st.button("🗑️", key=f"del_income_{idx}"):
                        delete_income(original_idx)
                        st.rerun()
            
            st.divider()
            st.metric("Total Income", f"€{sum(item['amount'] for item in st.session_state.data['income']):.2f}")
        else:
            st.info("No income recorded yet")
    
    with col2:
        st.subheader("Recent Expenses")
        if st.session_state.data['expenses']:
            expenses_df = pd.DataFrame(st.session_state.data['expenses'])
            expenses_df = expenses_df.sort_values('date', ascending=False).reset_index(drop=True)
            
            # Display with delete buttons
            for idx, row in expenses_df.iterrows():
                # Find original index in unsorted data
                original_idx = len(st.session_state.data['expenses']) - 1 - idx
                
                col_a, col_b, col_c, col_d, col_e = st.columns([2, 2, 2, 2, 1])
                with col_a:
                    st.text(row['date'])
                with col_b:
                    st.text(row['category'])
                with col_c:
                    st.text(row['description'])
                with col_d:
                    st.text(f"€{row['amount']:.2f}")
                with col_e:
                    if st.button("🗑️", key=f"del_expense_{idx}"):
                        delete_expense(original_idx)
                        st.rerun()
            
            st.divider()
            st.metric("Total Expenses", f"€{sum(item['amount'] for item in st.session_state.data['expenses']):.2f}")
        else:
            st.info("No expenses recorded yet")
    
    # Expenses by category
    if st.session_state.data['expenses']:
        st.divider()
        st.subheader("Expenses by Category")
        expenses_df = pd.DataFrame(st.session_state.data['expenses'])
        category_summary = expenses_df.groupby('category')['amount'].sum().sort_values(ascending=False)
        
        # Create pie chart
        import plotly.graph_objects as go
        
        # Get colors - red for highest, others in shades of blue/green
        colors = ['#ff4444']  # Red for the highest
        other_colors = ['#36a2eb', '#4bc0c0', '#9966ff', '#ff9f40', '#ffcd56', '#c9cbcf']
        colors.extend(other_colors[:len(category_summary)-1])
        
        fig = go.Figure(data=[go.Pie(
            labels=category_summary.index,
            values=category_summary.values,
            marker=dict(colors=colors),
            textinfo='label+percent',
            textposition='auto',
            hovertemplate='<b>%{label}</b><br>€%{value:.2f}<br>%{percent}<extra></extra>'
        )])
        
        fig.update_layout(
            showlegend=True,
            height=400,
            margin=dict(t=0, b=0, l=0, r=0)
        )
        
        st.plotly_chart(fig, use_container_width=True)