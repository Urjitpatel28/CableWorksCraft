using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Input;

namespace WpfUI.Command
{
    public class BaseCommand : ICommand
    {
        public event EventHandler CanExecuteChanged;

        public void RaiseCanExecuteChanged()
        {
            CanExecuteChanged?.Invoke(this, EventArgs.Empty);
        }

        public virtual bool CanExecute(object parameter)
        {
            // Default implementation always allows execution
            return true;
        }

        public virtual void Execute(object parameter)
        {
            // Default implementation does nothing
            // Override in derived class to provide specific functionality
        }        
    }
}