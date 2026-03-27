using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Controls;
using System.Windows.Data;

namespace WpfUI.Helpers
{
    public class LayerVisibilityConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is int selectedLayers && int.TryParse(parameter?.ToString(), out int layer))
                return selectedLayers >= layer;
            return false;
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
            => throw new NotImplementedException();
    }

    public class CoreTypeToHeightConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            return (value?.ToString() == "Shaped") ? 630 : 770;
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            throw new NotImplementedException(); // Not needed for one-way binding
        }
    }

    public class HalfMultiplierValidationRule : ValidationRule
    {
        public override ValidationResult Validate(object value, CultureInfo cultureInfo)
        {
            if (value is string strValue && double.TryParse(strValue, out double numValue))
            {
                if (numValue % 0.5 == 0)
                {
                    return ValidationResult.ValidResult;
                }
            }
            return new ValidationResult(false, "Value must be a multiple of 0.5");
        }
    }
}
