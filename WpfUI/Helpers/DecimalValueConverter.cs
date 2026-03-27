using System;
using System.Globalization;
using System.Windows.Data;

namespace WpfUI.Helpers
{
    public class DecimalValueConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is double doubleValue && doubleValue % 1 != 0)
                return true;  // Enable if it's a decimal value
            return false;   // Disable if it's not a decimal
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            return value is bool boolValue && boolValue ? 1.0 : 0.0;
        }
    }
}
