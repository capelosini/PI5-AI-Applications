export default class Cell {
    constructor(data) {
        this.level = data.level;
        this.professor = data.professor;
    }

    get isEmpty() {
        return this.level === 0;
    }

    get isMaxLevel() {
        return this.level === 4;
    }

    static fromBoard(boardData) {
        if (!boardData || !Array.isArray(boardData)) return [];
        return boardData.map(row => 
            row.map(cell => new Cell(cell))
        );
    }
}
