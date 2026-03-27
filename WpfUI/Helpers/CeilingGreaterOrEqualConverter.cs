using System;
using System.Globalization;
using System.Windows;
using System.Windows.Data;

namespace WpfUI.Helpers
{
    public class CeilingGreaterOrEqualConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is double num && parameter is string paramStr && int.TryParse(paramStr, out int target))
            {
                int ceiling = (int)Math.Floor(num);
                return ceiling >= target ? Visibility.Visible : Visibility.Collapsed;
            }
            return Visibility.Collapsed;
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            throw new NotImplementedException();
        }
    }

    public class CeilingLessOrEqualConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is double num && parameter is string paramStr && int.TryParse(paramStr, out int max))
            {
                int ceiling = (int)Math.Ceiling(num);
                return ceiling <= max;
            }
            return false;
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            throw new NotImplementedException();
        }
    }
}
