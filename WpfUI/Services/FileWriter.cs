using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using System;
using System.Diagnostics;
using System.IO;
using System.Windows;

namespace WpfUI.Services
{
    public class FileWriterService
    {
        public FileWriterService() { }
        public static string SaveToJson(object dataModel, string savePath)
        {
            // Serialize to JSON and save
            string json = JsonConvert.SerializeObject(dataModel, Formatting.Indented,
                new JsonSerializerSettings
                {
                    NullValueHandling = NullValueHandling.Ignore
                });


            string jsonFilePath = Path.Combine(savePath, "projectDetail.json");
            File.WriteAllText(jsonFilePath, json);
            Debug.Print("Data has been successfully saved to:\n" + jsonFilePath, "Save Successful", MessageBoxButton.OK, MessageBoxImage.Information);
            return jsonFilePath;
        }

        public static T ReadFromJson<T>(string filePathToJson, string jsonPath, string variableName)
        {
            try
            {
                // Read JSON data from file
                string json = File.ReadAllText(filePathToJson);
                JObject jsonObject = JObject.Parse(json);

                // Find the container object using JSONPath
                JToken container = jsonObject.SelectToken(jsonPath);

                // Verify container exists and is an object
                if (container == null || container.Type != JTokenType.Object)
                    return default(T);

                // Get the value from the container
                JToken valueToken = ((JObject)container)[variableName];
                return valueToken != null ? valueToken.Value<T>() : default(T);
            }
            catch
            {
                return default(T);
            }
        }
    }
}