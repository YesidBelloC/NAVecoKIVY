import smtplib
# https://www.youtube.com/watch?v=BsVQ_cBmEwg
server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
# server.starttls()
server.login("navecoexpleo@gmail.com", "NAVecoYes!d901208")
server.sendmail(
  "navecoexpleo@gmail.com",
  "navecoexpleo@gmail.com",
  "this message is from python")
server.quit()