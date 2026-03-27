using Microsoft.VisualStudio.TestTools.UnitTesting;
using System;
using System.Diagnostics;
using System.IO;
using WpfUI.Helpers;

namespace UnitTest
{
    [TestClass]
    public class UnitTest1
    {
        [TestMethod]
        public void TestMethod1()
        {           
            string command = @"""C:\\Program Files\\FreeCAD 1.0\\bin\\python.exe"" ""C:\\Temp\\CableConfigurator\\ProtoCode\\CircularCore_Rev1.py"" --jsonFile ""C:\\Temp\\CableConfigurator\\ProtoCode\\Json\\sample.json""";
                       
            WpfUI.Command.ExecuteCommand executeCommand = new WpfUI.Command.ExecuteCommand();
            executeCommand.RunCommandAsAdmin(command);
        }

        [TestMethod]
        public void Readxml()
        {

            string filePath = @"C:\Users\upatel\CADAI\ConfiguratorProjects - Documents\2024_U_006_TAMRA CABLES\00.Reference\CoreInLayerArrangement.xlsx"; // Update with your file path
            if (File.Exists(filePath))
            {
                var result = WpfUI.Helpers.ExcelReader.ReadExcel(filePath);

                // Print the result to verify
                foreach (var entry in result)
                {
                    Debug.Print($"Key: {entry.Key}, Values: [{string.Join(", ", entry.Value)}]");
                }
            }
            else
            {
                Console.WriteLine("File not found.");
            }

        }

        [TestMethod]
        public void ExcelWriter()
        {
            string filePath = @"C:\Temp\CableData.xlsx";
            //ExcelHelper.SaveDataToExcel();
            var color = ExcelHelper.ReadColorDataFromExcel(filePath);
        }
    }
}