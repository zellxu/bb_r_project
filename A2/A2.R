library(tidyverse)
library(dplyr)
library(GGally)
library(lubridate)
library(scales)

# Step 6: Join Elastic Map Reduce output with precipitation data ---------------------------------

EMRoutput = read_tsv("./EMRoutput.tsv", col_names = c("date", "hour", "drivers_onduty", "t_onduty", "t_occupied", "n_pass", "n_trip", "n_mile", "earnings"))
EMRoutput <- EMRoutput[order(EMRoutput$date,EMRoutput$hour),]
EMRoutput <- mutate(EMRoutput, DATE = as.POSIXct(paste(date, hour),tz = "UTC", format = "%Y-%m-%d %H"))
EMRoutput <- subset(EMRoutput, select = -c(date, hour))

precipitation = read_csv("./nyc_precipitation.csv", col_names = TRUE)
precipitation <- subset(precipitation, select = c(DATE,HPCP))

# HPCP: The amount of precipitation recorded at the station for the hour ENDING at the time specified for DATE above given in hundredths of inches or tenths of millimeters
# The values 99999 means the data value is missing. Hours with no precipitation are not shown.
#any(is.na(precipitation$HPCP)) returns FALSE
#any(precipitation$HPCP == 99999) returns FALSE
precipitation$DATE <- as.POSIXct(precipitation$DATE) - hours(1) # ending hr -> beginning hr

output <- left_join(EMRoutput, precipitation)

output <- output %>%  tidyr::separate(DATE, c("date", "hour"), sep = " ")
output <- output[,c("date", "hour", "HPCP", "drivers_onduty", "t_onduty", "t_occupied", "n_pass", "n_trip", "n_mile", "earnings")]
names(output)[3]<-"precip"
output$precip[which(is.na(output$precip))]=0

# Step 7: Investigate the effect of precipitation on hourly wages for taxi drivers, and the supply of and demand for taxis ---------------------------------

# Rain (binary indicator for whether it rained that hour)
output$rain = 0
output$rain[which(output$precip>0)] = 1

# RainLevel (No Rain, Light Rain (less than 0.098inch), Moderate Rain (less than 0.3inch), Heavy Rain (otherwise))
# reference from Wiki: https://en.wikipedia.org/wiki/Rain
output$rainLevel = "No rain"
output$rainLevel[which(output$precip>0 & output$precip<0.098)] = "Light Rain"
output$rainLevel[which(output$precip>=0.098 & output$precip<0.3)] = "Moderate Rain"
output$rainLevel[which(output$precip>=0.3)] = "Heavy Rain"

# Average earning
output$avgWage = output$earnings/output$drivers_onduty

raindf <- output %>% group_by(hour, rain) %>% summarize(avgWage = mean(avgWage)) %>% filter(rain==1)
noraindf <- output %>% group_by(hour, rain) %>% summarize(avgWage = mean(avgWage)) %>% filter(rain==0)
rain <- output %>% group_by(hour, rain) %>% filter(rain==1)
plot.data <- tibble(raindf$hour, raindf$avgWage, noraindf$avgWage)
colnames(plot.data) = c("hour", "avgWageRain","avgWageNoRain")

plot.data %>% ggplot() + 
  geom_line(data = plot.data, aes(x = hour, y = avgWageRain, color = "Rain", group = 1)) +
  geom_line(data = plot.data, aes(x = hour, y = avgWageNoRain, color = "noRain", group = 1)) + 
  geom_point(data = plot.data, aes(x = hour, y = avgWageNoRain, color = "noRain", group = 1)) +
  labs(x = "Time",  y = "average earning", color = 'Rained Or Not', title = "Average Wage by Hour")  +
  theme_bw() + scale_color_manual(values = c('Rain' = 'blue','noRain' = 'red'))

plot.data <- output %>% group_by()

output %>% ggplot() + 
  geom_line(data = output, aes(x = timeInterval, y = FGame, color = "Female")) +
  geom_line(data = output, aes(x = timeInterval, y = MGame, color = "Male")) + 
  labs(x = "Time",  y = "tweet count", color = 'Type', title = "Tweet count over 1 day by gender, keyword: game")  +
  theme_bw() + scale_color_manual(values = c('Female' = 'red','Male' = 'blue'))
ggsave(plot=plotG, file="./gameTweetPlot.pdf", width=10, height=5)
