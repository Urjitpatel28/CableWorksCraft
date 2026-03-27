using System;
using System.Diagnostics;
using System.Windows;

namespace WpfUI.Command
{
    public class ExecuteCommand
    {
        public void RunCommandAsAdmin(string command)
        {
            Process cmd = new Process();
            cmd.StartInfo.FileName = "cmd.exe";
            cmd.StartInfo.RedirectStandardInput = true;
            cmd.StartInfo.RedirectStandardOutput = true;
            cmd.StartInfo.CreateNoWindow = true;
            cmd.StartInfo.UseShellExecute = false;
            cmd.Start();

            cmd.StandardInput.WriteLine(command);
            cmd.StandardInput.Flush();
            cmd.StandardInput.WriteLine("exit");  // Ensure the cmd process exits cleanly by sending an exit command
            cmd.StandardInput.Close();

            Debug.Print(cmd.StandardOutput.ReadToEnd());
            cmd.WaitForExit();  // Waits for the process to exit
            cmd.Close();  // Explicitly close the process
            cmd.Dispose();  // Optionally dispose the process object
        }
    }
}