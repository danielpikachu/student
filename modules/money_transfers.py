<style>
.transaction-table {
    width: 100%;
    border-collapse: collapse;
    border: 1px solid #ddd;
}
.transaction-table th, .transaction-table td {
    border: 1px solid #ddd;
    padding: 10px;
}
.transaction-table th:nth-child(1),
.transaction-table td:nth-child(1) { width: 5%; text-align: center; }
.transaction-table th:nth-child(2),
.transaction-table td:nth-child(2) { width: 15%; }
.transaction-table th:nth-child(3),
.transaction-table td:nth-child(3) { width: 15%; text-align: right; }
.transaction-table th:nth-child(4),
.transaction-table td:nth-child(4) { width: 10%; }
.transaction-table th:nth-child(5),
.transaction-table td:nth-child(5) { width: 30%; }
.transaction-table th:nth-child(6),
.transaction-table td:nth-child(6) { width: 25%; }
.transaction-table th {
    background-color: #f5f5f5;
    font-weight: bold;
}
.income { color: green; }
.expense { color: red; }
</style>

<table class="transaction-table">
    <thead>
        <tr>
            <th>No.</th>
            <th>Date</th>
            <th>Amount ($)</th>
            <th>Category</th>
            <th>Description</th>
            <th>Handled By</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>1</td>
            <td>2025-11-02</td>
            <td class="expense">$100.00</td>
            <td>None</td>
            <td>Fundraiser proceeds</td>
            <td>Pikachu Da Best</td>
        </tr>
        <tr>
            <td>2</td>
            <td>2025-11-02</td>
            <td class="income">$100.00</td>
            <td>None</td>
            <td>Fundraiser proceeds</td>
            <td>Pikachu Da Best</td>
        </tr>
        <tr>
            <td>3</td>
            <td>2025-11-02</td>
            <td class="expense">$100.00</td>
            <td>None</td>
            <td>Fundraiser proceeds</td>
            <td>Pikachu Da Best</td>
        </tr>
    </tbody>
</table>
