using ClosedXML.Excel;
using System.Collections.Generic;
using System.Diagnostics;
using System.Threading.Tasks;

namespace WpfUI.Helpers
{
    public class ExcelReader
    {
        public static async Task<Dictionary<double, double[]>> ReadExcelAsync(string filePath)
        {
            return await Task.Run(() => ReadExcel(filePath));
        }

        public static Dictionary<double, double[]> ReadExcel(string filePath)
        {
            var data = new Dictionary<double, double[]>();

            // Open the Excel workbook
            using (var workbook = new XLWorkbook(filePath))
            {
                var worksheet = workbook.Worksheet(1); // Assuming the data is in the first worksheet

                int row = 2; // Starting from the second row (assuming first row is headers)

                while (!worksheet.Row(row).Cell(1).IsEmpty()) // Check if first column is not empty
                {
                    // Read the first column value as key
                    double key;
                    if (!double.TryParse(worksheet.Row(row).Cell(1).GetValue<string>(), out key))
                    {
                        Debug.Print($"Invalid value in column 1, row {row}. Expected a double.");
                        return null;
                    }

                    // Create a list to store non-zero values
                    var valuesList = new List<double>();

                    // Read the next six columns
                    for (int col = 2; col <= 7; col++) // Columns B to G (2 to 7)
                    {
                        string cellValue = worksheet.Row(row).Cell(col).GetValue<string>();

                        // Parse the value as double
                        double value;
                        if (double.TryParse(cellValue, out value) && value != 0)
                        {
                            valuesList.Add(value); // Add non-zero values to the list
                        }
                    }

                    // Add to the dictionary
                    data[key] = valuesList.ToArray();

                    row++;
                }
            }
            return data;
        }
    }
}