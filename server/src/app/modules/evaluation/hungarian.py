def maximum_weight_assignment(weights: list[list[float]]) -> list[tuple[int, int]]:
    if not weights or not weights[0]:
        return []
    if len(weights) <= len(weights[0]):
        return _minimum_cost_assignment([[-weight for weight in row] for row in weights])
    transposed = [list(column) for column in zip(*weights, strict=True)]
    return [
        (column, row)
        for row, column in _minimum_cost_assignment(
            [[-weight for weight in transposed_row] for transposed_row in transposed]
        )
    ]


def _minimum_cost_assignment(costs: list[list[float]]) -> list[tuple[int, int]]:
    row_count = len(costs)
    column_count = len(costs[0])
    potentials_by_row = [0.0] * (row_count + 1)
    potentials_by_column = [0.0] * (column_count + 1)
    matched_rows_by_column = [0] * (column_count + 1)
    predecessors = [0] * (column_count + 1)

    for row in range(1, row_count + 1):
        matched_rows_by_column[0] = row
        minimum_costs = [float("inf")] * (column_count + 1)
        used_columns = [False] * (column_count + 1)
        column = 0
        while True:
            used_columns[column] = True
            current_row = matched_rows_by_column[column]
            delta = float("inf")
            next_column = 0
            for candidate_column in range(1, column_count + 1):
                if used_columns[candidate_column]:
                    continue
                reduced_cost = (
                    costs[current_row - 1][candidate_column - 1]
                    - potentials_by_row[current_row]
                    - potentials_by_column[candidate_column]
                )
                if reduced_cost < minimum_costs[candidate_column]:
                    minimum_costs[candidate_column] = reduced_cost
                    predecessors[candidate_column] = column
                if minimum_costs[candidate_column] < delta:
                    delta = minimum_costs[candidate_column]
                    next_column = candidate_column
            for candidate_column in range(column_count + 1):
                if used_columns[candidate_column]:
                    potentials_by_row[matched_rows_by_column[candidate_column]] += delta
                    potentials_by_column[candidate_column] -= delta
                elif candidate_column > 0:
                    minimum_costs[candidate_column] -= delta
            column = next_column
            if matched_rows_by_column[column] == 0:
                break
        while True:
            previous_column = predecessors[column]
            matched_rows_by_column[column] = matched_rows_by_column[previous_column]
            column = previous_column
            if column == 0:
                break

    return [
        (row - 1, column - 1)
        for column, row in enumerate(matched_rows_by_column)
        if column > 0 and row > 0
    ]
