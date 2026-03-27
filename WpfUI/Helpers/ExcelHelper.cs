using ClosedXML.Excel;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;


namespace WpfUI.Helpers
{
    public static class ExcelHelper
    {
        private static readonly string FilePath = @"C:\Temp\CableData.xlsx"; // Change path as needed

        public static void SaveDataToExcel()
        {
            using (var workbook = new XLWorkbook())
            {
                // Create sheets and store data
                SaveListToSheet(workbook, "ConductorMaterial", new[] { "Copper", "Aluminium", "Tinned", "(None)" });
                SaveListToSheet(workbook, "InsulationMaterial", new[] { "XLPE", "(None)" });
                SaveListToSheet(workbook, "ConductorScreenMaterial", new[] { "Mico", "Non-Metalic", "Water Blocking", "(None)" });
                SaveListToSheet(workbook, "FillerMaterial", new[] { "PP", "XLPE", "PVC", "(None)" });
                SaveListToSheet(workbook, "InsulationScreenMaterial", new[] { "Polyster", "Fiber Glass", "(None)" });
                SaveListToSheet(workbook, "InnerSheathMaterial", new[] { "PVC", "XLPE", "HDPE", "(None)" });
                SaveListToSheet(workbook, "OuterSheathMaterial", new[] { "PVC", "St1" });
                SaveListToSheet(workbook, "InnerSheathColour", new[] { "Black", "(None)" });
                SaveListToSheet(workbook, "OuterSheathColour", new[] { "Black", "Red", "Red Stripe" });

                workbook.SaveAs(FilePath);
            }
        }

        private static void SaveListToSheet(XLWorkbook workbook, string sheetName, string[] items)
        {
            var worksheet = workbook.Worksheets.Add(sheetName);
            for (int i = 0; i < items.Length; i++)
            {
                worksheet.Cell(i + 1, 1).Value = items[i];
            }
        }


        public static Dictionary<string, string> ReadColorDataFromExcel(string filePath)
        {
            try
            {
                var colorDictionary = new Dictionary<string, string>();

                // Check if the file exists
                if (!File.Exists(filePath))
                {
                    throw new FileNotFoundException("Excel file not found.", filePath);
                }

                // Load the workbook
                using (var workbook = new XLWorkbook(filePath))
                {
                    // Get the first worksheet (adjust index/name if needed)
                    var worksheet = workbook.Worksheet("colors");

                    // Iterate through rows (skip header row)
                    foreach (var row in worksheet.RowsUsed().Skip(1))
                    {
                        // Read color name from Column 1
                        var colorName = row.Cell(1).Value.ToString();

                        // Read RGB value from Column 2
                        var rgbValue = row.Cell(2).Value.ToString();

                        // Add to dictionary
                        if (!string.IsNullOrEmpty(colorName) && !string.IsNullOrEmpty(rgbValue))
                        {
                            colorDictionary[colorName] = rgbValue;
                        }
                    }
                }

                return colorDictionary;
            }

            catch (Exception ex)
            {
               
                throw;
            }
        }

        public static ObservableCollection<string> ReadSingleColumnSheet(string filePath, string sheetName)
        {
            var collection = new ObservableCollection<string>();

            using (var workbook = new XLWorkbook(filePath))
            {
                var worksheet = workbook.Worksheet(sheetName);
                foreach (var row in worksheet.RowsUsed())
                {
                    var cellValue = row.Cell(1).GetString();
                    if (!string.IsNullOrWhiteSpace(cellValue))
                        collection.Add(cellValue);
                }
            }

            return collection;
        }
    }
}